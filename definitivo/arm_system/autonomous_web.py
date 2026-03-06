#!/usr/bin/env python3
"""
Interfaz web para el modo autonomo del brazo robotico.
Muestra video en vivo con detecciones superpuestas,
estado del robot, estadisticas y controles de pausa/stop/resume.
"""

import os
import sys
import time
import threading
import logging as log

from flask import Flask, Response, request, jsonify, render_template_string

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autonomous_brain import CerebroAutonomo

log.basicConfig(level=log.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
cerebro = None
hilo_autonomo = None


def obtener_cerebro():
    global cerebro
    if cerebro is None:
        cerebro = CerebroAutonomo(habilitar_hardware=True)
    return cerebro


# ------------------------------------------------------------------ #
# VIDEO STREAM
# ------------------------------------------------------------------ #

def generar_frames():
    """Genera frames MJPEG desde la camara del cerebro."""
    import cv2
    c = obtener_cerebro()
    while True:
        try:
            frame = c.frame_actual
            if frame is None:
                img = c._capturar_imagen()
                if img is not None:
                    c.frame_actual = img
                    frame = img

            if frame is not None:
                if c.detector_color and c.objetos:
                    objs_draw = [{'bbox': o.bbox, 'color': o.color,
                                  'clase': o.clase, 'confianza': o.confianza}
                                 for o in c.objetos]
                    recs_draw = [{'bbox': r.bbox, 'color': r.color,
                                  'centro': r.centro} for r in c.recipientes]
                    frame = c.detector_color.dibujar_resultados(frame, objs_draw, recs_draw)

                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            else:
                time.sleep(0.5)
        except Exception:
            time.sleep(1)

        time.sleep(0.1)


# ------------------------------------------------------------------ #
# RUTAS API
# ------------------------------------------------------------------ #

@app.route('/video_feed')
def video_feed():
    return Response(generar_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/estado')
def api_estado():
    c = obtener_cerebro()
    return jsonify(c.obtener_estado())


@app.route('/api/iniciar', methods=['POST'])
def api_iniciar():
    global hilo_autonomo
    c = obtener_cerebro()
    if hilo_autonomo and hilo_autonomo.is_alive():
        return jsonify({'ok': False, 'msg': 'Ya esta ejecutandose'})

    c._detener = False
    c._pausar = False
    ciclos = request.json.get('ciclos', 50) if request.is_json else 50
    hilo_autonomo = threading.Thread(target=c.ejecutar_ciclo_autonomo,
                                     args=(ciclos,), daemon=True)
    hilo_autonomo.start()
    return jsonify({'ok': True, 'msg': 'Modo autonomo iniciado'})


@app.route('/api/pausar', methods=['POST'])
def api_pausar():
    obtener_cerebro().pausar()
    return jsonify({'ok': True, 'msg': 'Pausado'})


@app.route('/api/reanudar', methods=['POST'])
def api_reanudar():
    obtener_cerebro().reanudar()
    return jsonify({'ok': True, 'msg': 'Reanudado'})


@app.route('/api/detener', methods=['POST'])
def api_detener():
    obtener_cerebro().detener()
    return jsonify({'ok': True, 'msg': 'Detenido'})


@app.route('/api/home', methods=['POST'])
def api_home():
    obtener_cerebro().robot.posicion_home()
    return jsonify({'ok': True, 'msg': 'Posicion HOME'})


@app.route('/api/escanear', methods=['POST'])
def api_escanear():
    c = obtener_cerebro()
    objs, recs = c._escanear_entorno()
    return jsonify({
        'ok': True,
        'objetos': [o.to_dict() for o in objs],
        'recipientes': [r.to_dict() for r in recs],
    })


@app.route('/api/mover', methods=['POST'])
def api_mover():
    """Control manual rapido: {'joint': 'shoulder', 'dir': 1, 'time': 0.5}"""
    data = request.get_json()
    c = obtener_cerebro()
    joint = data.get('joint', 'shoulder')
    direccion = int(data.get('dir', 0))
    tiempo = float(data.get('time', 0.5))
    velocidad = float(data.get('speed', 0.4))

    try:
        c.robot.controlador_servo.mover_por_tiempo(joint, direccion, tiempo, velocidad)
        return jsonify({'ok': True, 'msg': f'{joint} movido'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})


@app.route('/api/emergencia', methods=['POST'])
def api_emergencia():
    c = obtener_cerebro()
    c.detener()
    c.robot.controlador_servo.detener_todos()
    c.robot.resetear_tiempos()
    return jsonify({'ok': True, 'msg': 'PARADA DE EMERGENCIA'})


# ------------------------------------------------------------------ #
# HTML
# ------------------------------------------------------------------ #

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brazo Robotico Autonomo</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.top-bar{background:linear-gradient(135deg,#1e3a5f,#0f172a);padding:16px 24px;display:flex;align-items:center;gap:16px;border-bottom:1px solid #334155}
.top-bar h1{font-size:1.4rem;font-weight:700;background:linear-gradient(90deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.estado-badge{padding:4px 14px;border-radius:20px;font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
.estado-IDLE{background:#334155;color:#94a3b8}
.estado-ESCANEANDO{background:#0369a1;color:#e0f2fe}
.estado-PLANIFICANDO{background:#7c3aed;color:#ede9fe}
.estado-RECOGIENDO{background:#ea580c;color:#fff7ed}
.estado-TRANSPORTANDO{background:#0891b2;color:#ecfeff}
.estado-DEPOSITANDO{background:#16a34a;color:#f0fdf4}
.estado-RECUPERANDO_ERROR{background:#dc2626;color:#fef2f2}
.estado-PAUSADO{background:#ca8a04;color:#fefce8}
.estado-COMPLETADO{background:#059669;color:#ecfdf5}
.main{display:grid;grid-template-columns:1fr 380px;gap:16px;padding:16px;max-width:1400px;margin:0 auto}
@media(max-width:900px){.main{grid-template-columns:1fr}}
.video-panel{background:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155}
.video-panel img{width:100%;display:block;min-height:300px;background:#000}
.side{display:flex;flex-direction:column;gap:12px}
.card{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}
.card h3{font-size:.85rem;text-transform:uppercase;letter-spacing:.8px;color:#64748b;margin-bottom:10px}
.btn-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.btn{padding:10px;border:none;border-radius:8px;font-weight:600;font-size:.85rem;cursor:pointer;transition:all .2s}
.btn:active{transform:scale(.96)}
.btn-start{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn-pause{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff}
.btn-resume{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff}
.btn-stop{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
.btn-home{background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff}
.btn-scan{background:linear-gradient(135deg,#06b6d4,#0891b2);color:#fff}
.btn-emergency{background:#dc2626;color:#fff;grid-column:1/-1;font-size:1rem;padding:14px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(220,38,38,.4)}50%{box-shadow:0 0 0 8px rgba(220,38,38,0)}}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.stat{background:#0f172a;border-radius:8px;padding:10px;text-align:center}
.stat .val{font-size:1.5rem;font-weight:700;color:#38bdf8}
.stat .lbl{font-size:.7rem;color:#64748b;margin-top:2px}
.obj-list,.rec-list{max-height:150px;overflow-y:auto;font-size:.8rem}
.obj-item,.rec-item{padding:6px 8px;border-radius:6px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center}
.obj-item{background:#0f172a}
.rec-item{background:#0f172a}
.color-dot{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px}
.dot-rojo{background:#ef4444}.dot-azul{background:#3b82f6}.dot-verde{background:#22c55e}.dot-amarillo{background:#eab308}
.dot-naranja{background:#f97316}.dot-morado{background:#a855f7}.dot-desconocido{background:#6b7280}
.log-box{max-height:120px;overflow-y:auto;font-size:.75rem;background:#0f172a;border-radius:8px;padding:8px;font-family:monospace;color:#94a3b8}
.manual-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.btn-sm{padding:8px 4px;font-size:.75rem;border:none;border-radius:6px;cursor:pointer;background:#334155;color:#e2e8f0;font-weight:600}
.btn-sm:hover{background:#475569}
</style>
</head>
<body>

<div class="top-bar">
  <h1>Brazo Robotico Autonomo</h1>
  <span class="estado-badge estado-IDLE" id="badge-estado">IDLE</span>
</div>

<div class="main">
  <div>
    <div class="video-panel">
      <img id="video" src="/video_feed" alt="Video en vivo">
    </div>
    <div class="card" style="margin-top:12px">
      <h3>Control Manual Rapido</h3>
      <div class="manual-grid">
        <div></div>
        <button class="btn-sm" onclick="manualMove('shoulder',1)">Hombro +</button>
        <div></div>
        <button class="btn-sm" onclick="manualMove('elbow',-1)">Codo -</button>
        <button class="btn-sm" onclick="manualMove('wrist',1)">Muneca +</button>
        <button class="btn-sm" onclick="manualMove('elbow',1)">Codo +</button>
        <div></div>
        <button class="btn-sm" onclick="manualMove('shoulder',-1)">Hombro -</button>
        <div></div>
        <button class="btn-sm" onclick="manualMove('gripper',1)">Pinza Abrir</button>
        <button class="btn-sm" style="background:#475569" onclick="apiPost('/api/home')">HOME</button>
        <button class="btn-sm" onclick="manualMove('gripper',-1)">Pinza Cerrar</button>
      </div>
    </div>
  </div>

  <div class="side">
    <div class="card">
      <h3>Controles</h3>
      <div class="btn-grid">
        <button class="btn btn-start" onclick="apiPost('/api/iniciar')">Iniciar</button>
        <button class="btn btn-pause" onclick="apiPost('/api/pausar')">Pausar</button>
        <button class="btn btn-resume" onclick="apiPost('/api/reanudar')">Reanudar</button>
        <button class="btn btn-stop" onclick="apiPost('/api/detener')">Detener</button>
        <button class="btn btn-home" onclick="apiPost('/api/home')">Home</button>
        <button class="btn btn-scan" onclick="apiPost('/api/escanear')">Escanear</button>
        <button class="btn btn-emergency" onclick="apiPost('/api/emergencia')">EMERGENCIA</button>
      </div>
    </div>

    <div class="card">
      <h3>Estadisticas</h3>
      <div class="stat-grid">
        <div class="stat"><div class="val" id="st-detectados">0</div><div class="lbl">Detectados</div></div>
        <div class="stat"><div class="val" id="st-exitos">0</div><div class="lbl">Agarres OK</div></div>
        <div class="stat"><div class="val" id="st-fallos">0</div><div class="lbl">Fallos</div></div>
        <div class="stat"><div class="val" id="st-depositos">0</div><div class="lbl">Depositos</div></div>
        <div class="stat"><div class="val" id="st-recuperados">0</div><div class="lbl">Errores Recup.</div></div>
        <div class="stat"><div class="val" id="st-ciclos">0</div><div class="lbl">Ciclos</div></div>
      </div>
    </div>

    <div class="card">
      <h3>Objetos Detectados</h3>
      <div class="obj-list" id="obj-list"><em style="color:#64748b">Sin datos</em></div>
    </div>

    <div class="card">
      <h3>Recipientes</h3>
      <div class="rec-list" id="rec-list"><em style="color:#64748b">Sin datos</em></div>
    </div>

    <div class="card">
      <h3>Historial</h3>
      <div class="log-box" id="log-box">Esperando eventos...</div>
    </div>
  </div>
</div>

<script>
function apiPost(url, body){
  fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):'{}'})
  .then(r=>r.json()).then(d=>{if(d.msg)console.log(d.msg)}).catch(e=>console.error(e));
}
function manualMove(joint,dir){
  apiPost('/api/mover',{joint,dir,time:0.4,speed:0.4});
}

function actualizarUI(){
  fetch('/api/estado').then(r=>r.json()).then(d=>{
    const badge=document.getElementById('badge-estado');
    badge.textContent=d.estado;
    badge.className='estado-badge estado-'+d.estado;

    const s=d.estadisticas;
    document.getElementById('st-detectados').textContent=s.objetos_detectados;
    document.getElementById('st-exitos').textContent=s.agarres_exitosos;
    document.getElementById('st-fallos').textContent=s.agarres_fallidos;
    document.getElementById('st-depositos').textContent=s.depositos_exitosos;
    document.getElementById('st-recuperados').textContent=s.errores_recuperados;
    document.getElementById('st-ciclos').textContent=s.ciclos_completados;

    const ol=document.getElementById('obj-list');
    if(d.objetos.length){
      ol.innerHTML=d.objetos.map(o=>`<div class="obj-item"><span><span class="color-dot dot-${o.color}"></span>${o.clase}</span><span>${(o.confianza*100).toFixed(0)}%</span></div>`).join('');
    } else {ol.innerHTML='<em style="color:#64748b">Ninguno</em>'}

    const rl=document.getElementById('rec-list');
    if(d.recipientes.length){
      rl.innerHTML=d.recipientes.map(r=>`<div class="rec-item"><span><span class="color-dot dot-${r.color}"></span>${r.color}</span><span>${r.depositados} obj</span></div>`).join('');
    } else {rl.innerHTML='<em style="color:#64748b">Ninguno</em>'}

    const lb=document.getElementById('log-box');
    if(d.historial_reciente.length){
      lb.innerHTML=d.historial_reciente.slice(-8).reverse().map(h=>`<div>${h.timestamp.split('T')[1].split('.')[0]} [${h.tipo}] ${JSON.stringify(h.datos).substring(0,80)}</div>`).join('');
    }
  }).catch(()=>{});
}

setInterval(actualizarUI,1500);
actualizarUI();
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


if __name__ == '__main__':
    print("=" * 60)
    print("  BRAZO ROBOTICO AUTONOMO - Interfaz Web")
    print("  Abrir en navegador: http://<IP_RASPBERRY>:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
