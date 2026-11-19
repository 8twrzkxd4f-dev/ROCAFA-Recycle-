"""Solver-neutral preparation bundle, deliberately not an executable FSI deck."""
import io
import json
import math
import shutil
import zipfile
from simulation import config, cross


def availability():
    return {n: shutil.which(n) for n in ('foamRun','simpleFoam','fluent','lsdyna','ls-dyna','ccx')}


def surface(area, vent, n=96, rings=24):
    r=math.sqrt(area/math.pi); sphere=r/1.1; inner=vent/2
    def point(j,k):
        s=inner+(r-inner)*j/rings;a=k*2*math.pi/n;b=s/sphere
        return (sphere*math.sin(b)*math.cos(a),sphere*math.sin(b)*math.sin(a),sphere*(math.cos(b)-math.cos(1.1)))
    rows=['solid illustrative_canopy']
    for j in range(rings):
        for k in range(n):
            a,b,c,d=point(j,k),point(j,k+1),point(j+1,k+1),point(j+1,k)
            for tri in ((a,c,b),(a,d,c)):
                normal=cross([tri[1][i]-tri[0][i] for i in range(3)],[tri[2][i]-tri[0][i] for i in range(3)])
                norm=math.sqrt(sum(v*v for v in normal))
                if norm<1e-14:continue
                rows.append('facet normal '+' '.join(f'{v/norm:.8g}' for v in normal))
                rows.append('outer loop')
                rows += ['vertex '+' '.join(f'{v:.8g}' for v in pt) for pt in tri]
                rows += ['endloop','endfacet']
    rows.append('endsolid illustrative_canopy')
    return '\n'.join(rows)


def bundle(data):
    p=config(data.get('config',{})); materials=data.get('materials',{})
    if not isinstance(materials,dict):raise ValueError('材料資料必須為物件')
    # No inferred strengths/permeabilities. Preserve supplied values as unverified metadata.
    bio=io.BytesIO()
    manifest={'status':'PREPARATION_ONLY_NOT_SOLVED','units':'SI; z up for exported STL',
              'config':p,'materials_unverified':materials,'solver_paths':availability(),
              'geometry':'Illustrative spherical cap, not a measured flying shape or cutting pattern',
              'reference_area':'flat nominal pi D0^2/4, including vent; Cd must use same convention',
              'missing':['verified flying/folded geometry','fabric biaxial and shear curves','fabric thickness and areal mass',
                         'strain-dependent permeability','line load-extension and damping curves','contact/friction/initial stress',
                         'validated solver version and formulation','experimental uncertainty and acceptance criteria']}
    with zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        for name,default_vent in [('main',.14),('drogue',.08)]:
            area=p[name+'_area']; vent=data.get(name+'_vent_m',default_vent)
            try:vent=float(vent)
            except (ValueError,TypeError):raise ValueError('孔徑需為數值') from None
            if not math.isfinite(vent) or not 0<=vent<2*math.sqrt(area/math.pi):raise ValueError('孔徑超過傘徑')
            z.writestr('geometry/'+name+'_illustrative_surface.stl',surface(area,vent))
        templates={
            'drop_test.csv':'time_s,force_n,speed_mps\n',
            'mesh_study.csv':'h_m,cd\n',
            'fabric_warp.csv':'strain,force_per_width_n_per_m\n',
            'fabric_weft.csv':'strain,force_per_width_n_per_m\n',
            'fabric_shear.csv':'shear_angle_rad,force_per_width_n_per_m\n',
            'permeability.csv':'pressure_drop_pa,normal_velocity_mps,warp_strain,weft_strain\n',
            'line_extension.csv':'extension_m,tension_n,rate_mps\n',
            'fsi_convergence.csv':'mesh_size_m,dt_s,peak_tension_n,mass_error_percent,energy_error_percent\n'}
        for name,text in templates.items():z.writestr('templates/'+name,text)
        z.writestr('CFD_FSI_WORKFLOW.md',WORKFLOW)
    return bio.getvalue()


WORKFLOW='''# CFD / FSI 求解準備包（尚未執行）

## 幾何
STL 是公尺單位、Z 向上的開放球冠薄面，中央孔與傘緣開放；不是封閉固體，也不是可直接匯入所有網格器的完成模型。球冠來自示意映射，周向布料變形未解。流體求解前須確認實際傘形、法向、雙側薄壁/多孔界面、尾流域與幾何品質。不能用封孔修補冒充實際透氣傘。

## 固定傘形 CFD
1. 固定已量測或結構平衡後的傘形；用實際開傘階段速度而非火箭最大上升速度設定入口。
2. 統一名目參考面積、空氣密度、黏度、孔口、布料透氣壓降、入口湍流與壓力出口。
3. 以低馬赫流設定起步；穩態 RANS 不穩定時，需考慮非定常方法並報告時間平均及波動，不可將 LES 稱為穩態求解。
4. 至少三層網格；變更遠場域尺寸、尾流加密、時間步長及壁面處理，輸出 Cd、壓差、殘差與質量不平衡。
5. 匯出 mesh_study.csv，連同不確定度與風洞結果比對。

## 雙向 FSI
先完成布料經緯/剪切/雙軸、傘繩與透氣性試驗；未取得資料不可填入任意材料強度當作真實值。單元/材料卡須依選定 LS-DYNA 版本核對，不在本包中生成假定可執行的 deck。
依序做：固定/全開結構校準 → 固定流場載荷 → 全開雙向耦合 → 半折疊 → 實際折疊有限質量部署。
記錄接觸、初始應力、質量縮放、數值阻尼、守恆、added mass、透氣性、收口事件及耦合收斂。ICFD 與 ALE 是不同建模路線，不能一概稱為固定笛卡兒網格＋顯式求解。
輸出總繫帶與個別傘繩張力、投影面積、變形、壓力場、載荷時間序列與能量/質量殘差。需外部實際求解器才會有這些結果。

## V&V
Verification：解析基準、時間步長、網格與計算域敏感度、守恆誤差。
Validation：未用於標定的獨立風洞/投放量測；確認感測器與輸出物理量相同、採樣與濾波一致，帶上量測不確定度和事前定義驗收門檻。
工具內 1D/6DOF 氣動阻力歷程不等於傘繩 snatch force。單一剛體 6DOF 不包含兩物體相對鐘擺，不能視為 9DOF 模型。

## 取得求解器
優先詢問學校研究授權、工作站與競賽團隊支援。
LS-DYNA Student：https://ansys.synopsys.com/academic/students/ansys-ls-dyna-student
OpenFOAM Mac：https://www.openfoam.com/download/openfoam-installation-on-mac-using-docker
preCICE OpenFOAM adapter：https://precice.org/adapter-openfoam-overview
不自動安裝軟體、不代替授權、不宣稱已有可執行 CFD/FSI 專案。

## 技術依據
https://www.grc.nasa.gov/www/k-12/VirtualAero/BottleRocket/airplane/termvr.html
https://www.dynalook.com/conferences/international-conf-2010/Simulation-5-3.pdf
https://www.dynalook.com/conferences/12th-european-ls-dyna-conference-2019/fluid-structure-interaction/le-garrec_dynas.pdf
https://lsdyna.ansys.com/wp-content/uploads/attachments/generalized-porous-media-flow-in-icfd-ls-dyna-fsi-free-surface-rtm-and-parachute-modeling.pdf
'''
