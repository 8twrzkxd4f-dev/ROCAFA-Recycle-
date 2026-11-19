"""Research-level rigid-aggregate recovery models. No fabric/line shock solver."""
import bisect
import csv
import io
import math

G = 9.80665
DEFAULTS = dict(mass=19.471, height=3361., initial_speed=0., main_height=450.,
                main_area=6.05, drogue_area=2.12, main_cd=.8, drogue_cd=.75,
                drogue_delay=.5, drogue_fill=1., main_fill=1., reef_ratio=1.,
                reef_hold=1., release_fill=1., rho0=1.225, wind_x=0., wind_y=0.,
                dt=.04, max_time=600., tilt_deg=5., inertia_xy=16., inertia_z=.06,
                lever=.4, damping=2., retain_drogue=False, mode='1d')
BOUNDS = dict(mass=(1,200),height=(1,5000),initial_speed=(0,60),main_height=(0,5000),
              main_area=(.1,30),drogue_area=(.05,10),main_cd=(.1,3),drogue_cd=(.1,3),
              drogue_delay=(0,20),drogue_fill=(.1,15),main_fill=(.1,15),reef_ratio=(.05,1),
              reef_hold=(0,30),release_fill=(.1,15),rho0=(.5,1.5),wind_x=(-20,20),wind_y=(-20,20),
              dt=(.005,.1),max_time=(10,1000),tilt_deg=(0,60),inertia_xy=(1,500),
              inertia_z=(.01,20),lever=(0,3),damping=(0,20))


def config(data):
    p = dict(DEFAULTS)
    for key,(low,high) in BOUNDS.items():
        v = data.get(key,p[key])
        if isinstance(v,bool):
            raise ValueError(key+' 必須是數值')
        try:
            v = float(v)
        except (ValueError,TypeError):
            raise ValueError(key+' 必須是數值') from None
        if not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f'{key} 應介於 {low} 與 {high}')
        p[key] = v
    if p['main_height'] > p['height']:
        raise ValueError('主傘高度不得超過起始高度')
    p['mode'] = data.get('mode','1d')
    if p['mode'] not in ('1d','6dof'):
        raise ValueError('mode 應為 1d 或 6dof')
    p['retain_drogue'] = data.get('retain_drogue',False)
    if not isinstance(p['retain_drogue'],bool):
        raise ValueError('retain_drogue 必須是布林值')
    return p


def density(h, rho0):
    # ISA troposphere density, scaled by user-supplied sea-level density.
    return rho0 * (1 - .0065 * max(0,h) / 288.15) ** 4.25588


def smooth(x):
    x = min(1.,max(0.,x))
    return x*x*(3-2*x)


def fractions(t, p, main_time):
    drogue = smooth((t-p['drogue_delay'])/p['drogue_fill'])
    main = 0.
    if main_time is not None:
        age = t-main_time
        main = p['reef_ratio']*smooth(age/p['main_fill'])
        main += (1-p['reef_ratio'])*smooth((age-p['main_fill']-p['reef_hold'])/p['release_fill'])
        if not p['retain_drogue']:
            drogue = 0.
    return drogue,main


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def rotate(q,v):
    w,x,y,z=q
    return ((1-2*(y*y+z*z))*v[0]+2*(x*y-w*z)*v[1]+2*(x*z+w*y)*v[2],
            2*(x*y+w*z)*v[0]+(1-2*(x*x+z*z))*v[1]+2*(y*z-w*x)*v[2],
            2*(x*z-w*y)*v[0]+2*(y*z+w*x)*v[1]+(1-2*(x*x+y*y))*v[2])


def loads(t,y,p,main_time):
    fd,fm=fractions(t,p,main_time)
    cda_d=p['drogue_area']*p['drogue_cd']*fd
    cda_m=p['main_area']*p['main_cd']*fm
    wx,wy=(p['wind_x'],p['wind_y']) if p['mode']=='6dof' else (0.,0.)
    rel=(y[3]-wx,y[4]-wy,y[5])
    speed=math.sqrt(sum(v*v for v in rel))
    qdyn=.5*density(y[2],p['rho0'])*speed*speed
    force=qdyn*(cda_d+cda_m)
    vec=tuple(-v*force/speed for v in rel) if speed>1e-12 else (0.,0.,0.)
    return vec,force,qdyn*cda_d,qdyn*cda_m,fd,fm,speed


def derivative(t,y,p,mt):
    vec,*_=loads(t,y,p,mt)
    result=[y[3],y[4],y[5],vec[0]/p['mass'],vec[1]/p['mass'],vec[2]/p['mass']-G]
    if p['mode']=='6dof':
        q=y[6:10]; omega=y[10:13];w,x,yy,z=q;ox,oy,oz=omega
        result += [(-x*ox-yy*oy-z*oz)/2,(w*ox+yy*oz-z*oy)/2,
                   (w*oy+z*ox-x*oz)/2,(w*oz+x*oy-yy*ox)/2]
        fb=rotate((w,-x,-yy,-z),vec)
        torque=list(cross((0,0,p['lever']),fb))
        inertia=(p['inertia_xy'],p['inertia_xy'],p['inertia_z'])
        gyro=cross(omega,[inertia[i]*omega[i] for i in range(3)])
        result += [(torque[i]-p['damping']*omega[i]-gyro[i])/inertia[i] for i in range(3)]
    return result


def rk4(t,y,h,p,mt):
    a=derivative(t,y,p,mt)
    b=derivative(t+h/2,[v+h*a[i]/2 for i,v in enumerate(y)],p,mt)
    c=derivative(t+h/2,[v+h*b[i]/2 for i,v in enumerate(y)],p,mt)
    d=derivative(t+h,[v+h*c[i] for i,v in enumerate(y)],p,mt)
    out=[v+h*(a[i]+2*b[i]+2*c[i]+d[i])/6 for i,v in enumerate(y)]
    if not all(math.isfinite(v) for v in out) or max(abs(v) for v in out)>1e9:
        raise ValueError('積分不穩定；請減小時間步長或檢查慣量、阻尼與受力偏距')
    if p['mode']=='6dof':
        norm=math.sqrt(sum(v*v for v in out[6:10]))
        out[6:10]=[v/norm for v in out[6:10]]
    return out


def run(data, step=None):
    p=config(data); dt=p['dt'] if step is None else step
    if not 0.001<=dt<=.1:
        raise ValueError('時間步長超出允許範圍')
    y=[0.,0.,p['height'],0.,0.,-p['initial_speed']]
    if p['mode']=='6dof':
        angle=math.radians(p['tilt_deg'])/2
        y += [math.cos(angle),0.,math.sin(angle),0.,0.,0.,0.]
    t=0.;mt=0. if p['main_height']==p['height'] else None
    rows=[]; peak=0.; peak_time=0.;peak_main=0.;peak_drogue=0.; tilt_max=0.;next_store=0.
    event_times=[p['drogue_delay'],p['drogue_delay']+p['drogue_fill']]
    def record(force_store=False):
        nonlocal peak,peak_time,peak_main,peak_drogue,tilt_max,next_store
        vec,f,fd,fm,df,mf,v=loads(t,y,p,mt)
        tilt=math.degrees(math.acos(max(-1.,min(1.,rotate(y[6:10],(0,0,1))[2])))) if p['mode']=='6dof' else 0.
        if f>peak:peak=f;peak_time=t
        peak_main=max(peak_main,fm);peak_drogue=max(peak_drogue,fd);tilt_max=max(tilt_max,tilt)
        if force_store or t>=next_store-1e-10:
            rows.append(dict(time_s=t,height_m=max(0.,y[2]),speed_mps=-y[5],airspeed_mps=v,
                             force_n=f,main_force_n=fm,drogue_force_n=fd,net_deceleration_g=vec[2]/p['mass']/G-1,
                             main_fraction=mf,drogue_fraction=df,x_m=y[0],y_m=y[1],tilt_deg=tilt))
            next_store=t+.2
    record(True)
    while y[2]>0 and t<p['max_time']-1e-9:
        h=min(dt,p['max_time']-t)
        # Resolve discontinuities in stage configuration exactly.
        events=list(event_times)
        if mt is not None:events += [mt+p['main_fill'],mt+p['main_fill']+p['reef_hold'],mt+p['main_fill']+p['reef_hold']+p['release_fill']]
        upcoming=[e-t for e in events if e>t+1e-9]
        if upcoming:h=min(h,min(upcoming))
        yn=rk4(t,y,h,p,mt)
        threshold=p['main_height'] if mt is None and p['main_height']>0 else 0.
        if y[2]>threshold and yn[2]<=threshold:
            lo,hi=0.,h
            for _ in range(26):
                mid=(lo+hi)/2
                if rk4(t,y,mid,p,mt)[2]>threshold:lo=mid
                else:hi=mid
            h=hi;yn=rk4(t,y,h,p,mt);yn[2]=threshold
        t+=h;y=yn
        record()
        if mt is None and 0<y[2]<=p['main_height']+1e-8:
            record(True);mt=t;record(True)
        if len(rows)>10000:raise ValueError('輸出資料過多')
    record(True)
    landed=y[2]<=0
    return dict(config=p,rows=rows,summary=dict(landed=landed,duration_s=t,landing_speed_mps=-y[5] if landed else None,
                ground_speed_mps=math.sqrt(sum(v*v for v in y[3:6])) if landed else None,
                aero_peak_n=peak,peak_time_s=peak_time,main_aero_peak_n=peak_main,drogue_aero_peak_n=peak_drogue,
                main_trigger_s=mt,drift_m=math.hypot(y[0],y[1]),max_tilt_deg=tilt_max),
                model_status='uncalibrated',snatch_force_n=None,
                limitations=['經驗 smoothstep 阻力面積成長；參數未標定','氣動力不是已驗證的傘繩峰值張力；不含 added mass 或 snatch',
                             '6DOF 為單一剛體等效物；未建立傘衣與火箭間相對鐘擺運動','風為固定水平風；高度假設海平面射場'])


def convergence(data):
    p=config(data); results=[]
    for dt in (p['dt'],p['dt']/2,p['dt']/4):
        result=run(p,dt)
        results.append(dict(dt_s=dt,**result['summary']))
    diffs={}
    for key in ('aero_peak_n','landing_speed_mps','duration_s','drift_m'):
        a,b=results[-2][key],results[-1][key]
        diffs[key]=None if a is None or b is None else abs(a-b)/max(abs(b),1e-9)*100
    return dict(levels=results,fine_relative_change_percent=diffs,
                note='時間步長敏感度，不代表物理模型已驗證；峰值在每步取樣，三次均須落地才能比較落地速度。')


def compare_csv(data):
    cfg=data.get('config',{})
    text=data.get('csv','')
    if not isinstance(text,str) or len(text)>500000:raise ValueError('CSV 大小限制為 500 KB')
    try:offset=float(data.get('time_offset',0))
    except (ValueError,TypeError):raise ValueError('時間偏移須為數值') from None
    if not math.isfinite(offset) or abs(offset)>1000:raise ValueError('時間偏移不合理')
    rows=list(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))))
    if not 3<=len(rows)<=5000:raise ValueError('CSV 需有 3–5000 列，標頭 time_s,force_n 或 time_s,speed_mps')
    keys=[k for k in ('force_n','speed_mps') if k in rows[0]]
    if not keys or 'time_s' not in rows[0]:raise ValueError('CSV 必須有 time_s 及 force_n 或 speed_mps')
    obs=[]
    try:
        for row in rows:obs.append({'time_s':float(row['time_s'])+offset,**{k:float(row[k]) for k in keys}})
    except (ValueError,TypeError):raise ValueError('CSV 包含非數值或空白') from None
    if any(not all(math.isfinite(v) for v in r.values()) for r in obs):raise ValueError('CSV 不能包含 NaN/Inf')
    if any(b['time_s']<=a['time_s'] for a,b in zip(obs,obs[1:])):raise ValueError('CSV 時間必須嚴格遞增')
    sim=run(cfg); sample={r['time_s']:r for r in sim['rows']}; times=sorted(sample)
    aligned=[]
    for row in obs:
        t=row['time_s']
        if t<times[0] or t>times[-1]:continue
        i=min(len(times)-1,max(1,bisect.bisect_left(times,t)))
        a,b=sample[times[i-1]],sample[times[i]];w=(t-times[i-1])/(times[i]-times[i-1])
        aligned.append(dict(time_s=t,**{k:row[k] for k in keys},**{'sim_'+k:a[k]*(1-w)+b[k]*w for k in keys}))
    if len(aligned)<3:raise ValueError('模擬與量測的重疊時間範圍內少於三筆資料')
    metrics={}
    for k in keys:
        errors=[r['sim_'+k]-r[k] for r in aligned]
        metrics[k]=dict(rmse=math.sqrt(sum(e*e for e in errors)/len(errors)),bias=sum(errors)/len(errors),
                        mae=sum(abs(e) for e in errors)/len(errors),
                        observed_peak=max(r[k] for r in aligned),simulated_peak_at_observation_times=max(r['sim_'+k] for r in aligned))
    return dict(metrics=metrics,aligned=aligned,matched_count=len(aligned),excluded_count=len(obs)-len(aligned),
                note='依重疊時段線性插值、不外插、不自動時間對齊；須確認量測與模型對應的物理量。未提供不確定度或驗收門檻，不能宣稱 Validation 通過。')


def mesh_study(text):
    rows=list(csv.DictReader(io.StringIO(str(text).lstrip('\ufeff'))))
    if not 3<=len(rows)<=30:raise ValueError('需 3–30 層網格，CSV 標頭 h_m,cd')
    try:levels=sorted([{'h_m':float(r['h_m']),'cd':float(r['cd'])} for r in rows],key=lambda r:-r['h_m'])
    except (KeyError,ValueError,TypeError):raise ValueError('網格 CSV 必須包含數值 h_m,cd') from None
    if any(not all(math.isfinite(v) and v>0 for v in r.values()) for r in levels):raise ValueError('網格尺寸與 Cd 必須為有限正值')
    if len({r['h_m'] for r in levels})!=len(levels):raise ValueError('網格尺寸不得重複')
    for i,r in enumerate(levels):r['relative_change_percent']=None if i==0 else abs(r['cd']-levels[i-1]['cd'])/r['cd']*100
    return dict(levels=levels,note='只報告網格敏感度；未計算 GCI，未證明漸近收斂；須同步檢查計算域、殘差、質量守恆與壓力場。')
