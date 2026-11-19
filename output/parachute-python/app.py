#!/usr/bin/env python3
"""本機降落傘設計工具；僅使用 Python 標準函式庫。"""
import json
import math
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from simulation import run, convergence, compare_csv, mesh_study
from project_pack import availability, bundle

HERE = Path(__file__).resolve().parent
G = 9.80665
COMPUTE_LOCK = threading.Lock()


def calculate(p):
    """單傘、定 Cd；主傘落地速度採瞬間充氣與均勻密度的理想解。"""
    limits = {'mass': (.01, 1000), 'diameter': (.5, 6), 'cd': (.05, 5),
              'rho_open': (.05, 2), 'rho_land': (.05, 2),
              'speed': (0, 200), 'height': (0, 10000), 'target': (.01, 100)}
    vals = {}
    for name, (low, high) in limits.items():
        try:
            value = float(p[name])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f'{name} 必須是數值') from None
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{name} 應介於 {low} 與 {high}')
        vals[name] = value
    m, d, cd = vals['mass'], vals['diameter'], vals['cd']
    area = math.pi * (d / 2) ** 2  # Flat nominal area, matching the input Cd.
    speed, h = vals['speed'], vals['height']
    weight = m * G
    drag = .5 * vals['rho_open'] * cd * area * speed**2
    vt = math.sqrt(2 * weight / (vals['rho_land'] * cd * area))
    # dv/dt=g-kv²/m; integrating v dv/dh at constant rho gives v(h).
    k = .5 * vals['rho_land'] * cd * area
    landing = math.sqrt(max(0, vt**2 + (speed**2 - vt**2) * math.exp(-2*k*h/m)))
    return {'area': area, 'weight_n': weight, 'dynamic_pressure_pa': .5 * vals['rho_open'] * speed**2,
            'drag_n': drag, 'net_deceleration_g': (drag-weight)/weight,
            'terminal_mps': vt, 'ideal_landing_mps': landing,
            'target_mps': vals['target'], 'meets_target_estimate': landing <= vals['target']}


def build_page():
    workshop = (HERE / 'workshop.html').read_text(encoding='utf-8')
    shape = (HERE / 'shape.html').read_text(encoding='utf-8')
    # Reuse the existing geometry renderer and connect its specifications to the form.
    needle = 'restore(window.openai?.widgetState);sync();new ResizeObserver(draw).observe(canvas);'
    hook = '''window.updateParachute3D = (type, p) => {
      const skirt = .8102*p.d/2;
      if (p.l < skirt || !Number.isFinite(p.d) || !Number.isInteger(p.n)) return false;
      specs[type].area=Math.PI*p.d*p.d/4; specs[type].n=p.n;
      specs[type].L=p.l; specs[type].vent=p.v/1000;
      state.mode=type; sync(); draw(); return true;
    };
    restore(window.openai?.widgetState);sync();new ResizeObserver(draw).observe(canvas);'''
    if needle not in shape:
        raise RuntimeError('3D renderer hook missing')
    shape = shape.replace(needle, hook).replace('<div class="viz-row"><span id="pc-spec">', '<div class="viz-row" hidden><span id="pc-spec">')
    return ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>圓形降落傘設計與氣動估算</title><style>'
            ':root{--foreground:#183043;--background:#fff;--muted-foreground:#526579;'
            '--border:#c2ccd4;--viz-series-1:#d56822;--viz-series-2:#2d8496;'
            'font:16px system-ui,sans-serif;color:var(--foreground)}'
            'body{max-width:1050px;margin:auto;padding:20px}h1,h2{margin:20px 0 12px}'
            '.viz-controls,.viz-row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}'
            '.form-label{display:flex;flex-direction:column;gap:5px}.form-control,.form-select,button{'
            'font:inherit;padding:7px;border:1px solid var(--border);border-radius:5px;background:white;color:inherit}'
            '.form-range{max-width:180px}.form-check{display:flex;gap:5px;align-items:center}'
            '.text-muted{color:var(--muted-foreground)}.text-small{font-size:14px}'
            '.text-destructive{color:#aa2530}.viz-controls{margin:12px 0}'
            '#pc-spec{display:none}#pw-physics{border-top:1px solid var(--border);margin-top:20px}'
            '.note{color:#526579;line-height:1.5}.pw-physics-results{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin:16px 0}'
            '</style></head><body><h1>圓形降落傘設計與氣動估算</h1>'
            '<nav class="viz-controls"><a href="#parachute-workshop">裁片與外型</a><a href="#vv-dynamic">1D／6DOF</a><a href="#vv-cfd">CFD／FSI</a><a href="#vv-validation">V&amp;V</a></nav>'
            + workshop + '<h2>3D 外型與展開示意</h2>' + shape
            + (HERE / 'physics.html').read_text(encoding='utf-8')
            + (HERE / 'vv.html').read_text(encoding='utf-8') + '</body></html>')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/':
            body = build_page().encode('utf-8')
            self.reply(200, 'text/html; charset=utf-8', body)
        elif url.path == '/api/solvers':
            self.json_reply(200,availability())
        elif url.path == '/api/calculate':
            try:
                p = {k: v[0] for k, v in parse_qs(url.query).items()}
                body = json.dumps(calculate(p), ensure_ascii=False).encode('utf-8')
                self.reply(200, 'application/json; charset=utf-8', body)
            except ValueError as exc:
                self.reply(400, 'application/json; charset=utf-8', json.dumps({'error':str(exc)}, ensure_ascii=False).encode('utf-8'))
        else:
            self.reply(404, 'text/plain; charset=utf-8', b'Not found')

    def json_reply(self,status,data):
        self.reply(status,'application/json; charset=utf-8',json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8'))

    def do_POST(self):
        route=urlsplit(self.path).path
        if route not in ('/api/simulate','/api/convergence','/api/validate','/api/mesh-study','/api/project'):
            self.json_reply(404,{'error':'找不到此操作'});return
        origin=self.headers.get('Origin')
        if origin and urlsplit(origin).netloc != self.headers.get('Host'):
            self.json_reply(403,{'error':'只接受同來源本機操作'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=1000000:raise ValueError('請求大小應介於 1 byte 與 1 MB')
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict):raise ValueError('請求需為 JSON 物件')
        except (ValueError,UnicodeDecodeError) as exc:
            self.json_reply(400,{'error':str(exc)});return
        if not COMPUTE_LOCK.acquire(blocking=False):
            self.json_reply(409,{'error':'已有計算執行中，請稍後再試'});return
        try:
            if route=='/api/project':
                self.reply(200,'application/zip',bundle(payload))
            else:
                functions={'/api/simulate':run,'/api/convergence':convergence,'/api/validate':compare_csv,
                           '/api/mesh-study':lambda p:mesh_study(p.get('csv',''))}
                self.json_reply(200,functions[route](payload))
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            self.json_reply(400,{'error':str(exc)})
        finally:
            COMPUTE_LOCK.release()

    def reply(self, status, content_type, body):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    port = int(os.environ.get('PARACHUTE_PORT', '8765'))
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'開啟 http://127.0.0.1:{server.server_port} （Ctrl+C 停止）', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
