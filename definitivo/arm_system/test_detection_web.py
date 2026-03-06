#!/usr/bin/env python3
"""
Detección de objetos en tiempo real con stream web
Visualiza la cámara desde el navegador en http://<ip-raspberry>:5000
"""
import cv2
import time
import subprocess
import numpy as np
from flask import Flask, Response
from ultralytics import YOLO
from control.robot_controller import ControladorRobotico
import threading

# Flask app
app = Flask(__name__)

# Cargar el modelo YOLO
print("Cargando modelo YOLO...")
model = YOLO("perception/vision/detection/models/torch/yolo11n.pt")
print("Modelo cargado.")

# Inicializar controlador del brazo (SIN motor paso a paso)
print("Inicializando controlador del brazo...")
robot = ControladorRobotico(habilitar_stepper=False)

# Configuración
WIDTH = 1280  # ✅ MAYOR RESOLUCIÓN = Mayor campo de visión
HEIGHT = 720  # ✅ Aspect ratio 16:9 para mejor visión periférica
FPS = 15      # ✅ Reducido para mejor rendimiento (suficiente para detección)
TARGET_CLASSES = ['bottle', 'cup', 'cell phone', 'book']
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
DEAD_ZONE_X = 100  # Zona muerta proporcional a nueva resolución
DEAD_ZONE_Y = 50   # ✅ REDUCIDO para permitir acercarse más (antes: 80px)

# Variables globales
auto_movement_enabled = True  # ¡ACTIVADO AUTOMÁTICAMENTE AL INICIAR!
last_frame = None
last_annotated_frame = None  # Frame con detecciones dibujadas
frame_lock = threading.Lock()
last_movement_time = 0
MOVEMENT_COOLDOWN = 0.8  # Aumentado para movimientos más controlados
detection_results = None  # Cache de detecciones
results_lock = threading.Lock()
object_centered_count = 0  # Contador de frames centrados
CENTERED_THRESHOLD = 5  # Frames necesarios centrado para considerar "listo para agarrar"
grab_in_progress = False  # Flag para evitar múltiples agarres

def calculate_movement(obj_x, obj_y):
    """Calcular movimiento necesario"""
    error_x = obj_x - CENTER_X
    error_y = obj_y - CENTER_Y
    
    if abs(error_x) < DEAD_ZONE_X:
        error_x = 0
    if abs(error_y) < DEAD_ZONE_Y:
        error_y = 0
    
    if error_x == 0 and error_y == 0:
        return None
    
    # TIEMPOS MÁS CORTOS para movimientos más suaves y controlados
    time_horizontal = max(0.1, min(abs(error_x) / WIDTH * 0.3, 0.25))  # Máximo 0.25s
    time_vertical = max(0.1, min(abs(error_y) / HEIGHT * 0.25, 0.2))  # Máximo 0.2s
    
    dir_horizontal = 1 if error_x > 0 else -1
    dir_vertical = 1 if error_y > 0 else -1
    
    return {
        'horizontal': (dir_horizontal, time_horizontal) if error_x != 0 else None,
        'vertical': (dir_vertical, time_vertical) if error_y != 0 else None
    }

def move_to_object(movement):
    """Mover el brazo"""
    global last_movement_time
    
    if movement is None:
        return True
    
    current_time = time.time()
    if current_time - last_movement_time < MOVEMENT_COOLDOWN:
        return False
    
    try:
        # SOLO SERVOS - comentar motor paso a paso hasta arreglarlo
        # if movement['horizontal']:
        #     direction, duration = movement['horizontal']
        #     distance_mm = int(duration * 30)
        #     print(f"  → HORIZONTAL: dir={direction}, dist={distance_mm}mm")
        #     robot.mover_brazo(distance_mm, direccion=direction, velocidad=800)
        
        if movement['vertical']:
            direction, duration = movement['vertical']
            # Movimientos MUY CORTOS (máx 0.2s)
            duration = min(duration, 0.2)
            print(f"  ↕ VERTICAL: dir={direction}, tiempo={duration:.2f}s")
            robot.mover_hombro_tiempo(direction, duration, velocidad=0.3)
            
            # IMPORTANTE: Detener explícitamente el servo
            time.sleep(0.1)  # Pequeño delay
            robot.controlador_servo.detener_servo('hombro')
            print(f"  ⏹ Servo DETENIDO")
            
    except Exception as e:
        print(f"  ✗ ERROR al mover: {e}")
        return False
    
    last_movement_time = current_time
    return False

def capture_frames():
    """Thread para capturar frames RAW (sin detección)"""
    global last_frame
    
    cmd = [
        'rpicam-vid',
        '--inline',
        '--codec', 'mjpeg',
        '--width', str(WIDTH),
        '--height', str(HEIGHT),
        '--framerate', str(FPS),
        '-t', '0',
        '-o', '-',
        '--nopreview',
        '--rotation', '180'
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=10**8  # Buffer grande para resolución 1280x720
    )
    
    jpeg_buffer = b''
    
    print(f"Stream de cámara iniciado: {WIDTH}x{HEIGHT} @ {FPS}fps")
    
    try:
        while True:
            chunk = process.stdout.read(8192)  # ✅ Buffer mayor para 720p (antes: 4096)
            if not chunk:
                break
            
            jpeg_buffer += chunk
            
            start_marker = jpeg_buffer.find(b'\xff\xd8')
            end_marker = jpeg_buffer.find(b'\xff\xd9')
            
            if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
                jpeg_data = jpeg_buffer[start_marker:end_marker+2]
                jpeg_buffer = jpeg_buffer[end_marker+2:]
                
                frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    with frame_lock:
                        last_frame = frame.copy()
    
    finally:
        process.terminate()
        process.wait()

def detection_thread():
    """Thread dedicado SOLO a detección YOLO"""
    global detection_results, auto_movement_enabled, object_centered_count, grab_in_progress
    
    print("Thread de detección iniciado...")
    frame_count = 0
    
    while True:
        # Obtener frame
        with frame_lock:
            if last_frame is None:
                time.sleep(0.1)
                continue
            frame = last_frame.copy()
        
        frame_count += 1
        
        # ✅ Detectar CADA FRAME (no saltear) - Pi 5 puede manejarlo con FPS reducido
        # Antes: cada 3 frames → Ahora: cada frame
        
        # DETECCIÓN YOLO - OPTIMIZADA
        start_time = time.time()
        # ✅ imgsz=416 para MAYOR VELOCIDAD (en lugar de 640)
        # Suficiente para detectar objetos grandes de cerca
        results = model(frame, conf=0.45, verbose=False, imgsz=416)  # ✅ Confianza reducida + tamaño menor
        latency = (time.time() - start_time) * 1000
        
        boxes_obj = results[0].boxes
        
        best_detection = None
        best_confidence = 0
        target_center_x = None
        target_center_y = None
        all_detections = []
        
        if boxes_obj is not None and len(boxes_obj) > 0:
            bboxes = boxes_obj.xyxy.cpu().numpy()
            confs = boxes_obj.conf.cpu().numpy()
            classes = boxes_obj.cls.cpu().numpy()
            
            for i, box in enumerate(bboxes):
                x1, y1, x2, y2 = map(int, box)
                class_name = model.names[int(classes[i])]
                conf = float(confs[i])
                
                # Calcular tamaño del objeto (para saber si está cerca)
                box_width = x2 - x1
                box_height = y2 - y1
                box_area = box_width * box_height
                
                all_detections.append({
                    'box': (x1, y1, x2, y2),
                    'class': class_name,
                    'conf': conf,
                    'is_target': class_name in TARGET_CLASSES,
                    'area': box_area,
                    'width': box_width,
                    'height': box_height
                })
                
                if class_name in TARGET_CLASSES and conf > best_confidence:
                    best_detection = (class_name, conf, box)
                    best_confidence = conf
                    target_center_x = (x1 + x2) // 2
                    target_center_y = (y1 + y2) // 2
        
        # Guardar resultados
        with results_lock:
            detection_results = {
                'detections': all_detections,
                'best': best_detection,
                'target_pos': (target_center_x, target_center_y) if target_center_x else None,
                'latency': latency,
                'timestamp': time.time()
            }
        
        # Mover si auto está activado
        if best_detection and auto_movement_enabled and target_center_x and not grab_in_progress:
            movement = calculate_movement(target_center_x, target_center_y)
            
            # DEBUG: Imprimir siempre lo que está detectando
            class_name = best_detection[0]
            error_x = target_center_x - CENTER_X
            error_y = target_center_y - CENTER_Y
            
            # Calcular si objeto está lo suficientemente cerca (por tamaño)
            # Buscar el objeto detectado en all_detections para obtener su área
            target_area = 0
            for det in all_detections:
                if det['class'] == class_name and det['is_target']:
                    target_area = det['area']
                    break
            
            # Objeto "cerca" si ocupa más del 8% de la pantalla (1280x720 = 921,600px)
            total_pixels = WIDTH * HEIGHT
            is_close = (target_area / total_pixels) > 0.08  # 8% de la pantalla
            
            print(f"\n[DEBUG] Detectado: {class_name}")
            print(f"  Posición: ({target_center_x}, {target_center_y})")
            print(f"  Centro: ({CENTER_X}, {CENTER_Y})")
            print(f"  Error X: {error_x} (zona muerta: ±{DEAD_ZONE_X})")
            print(f"  Error Y: {error_y} (zona muerta: ±{DEAD_ZONE_Y})")
            print(f"  Área objeto: {target_area}px² ({target_area/total_pixels*100:.1f}% pantalla)")
            print(f"  ¿Está cerca?: {'SÍ ✓' if is_close else 'NO'}")
            print(f"  Movimiento calculado: {movement}")
            
            if movement:
                # Resetear contador si se está moviendo
                object_centered_count = 0
                print(f"[AUTO] Target: {class_name} - MOVIENDO...")
                move_to_object(movement)
            else:
                # Objeto centrado
                if is_close:
                    object_centered_count += 1
                    print(f"[AUTO] Target: {class_name} CENTRADO ✓ [{object_centered_count}/{CENTERED_THRESHOLD}]")
                    
                    # Si está centrado y cerca por suficientes frames → AGARRAR
                    if object_centered_count >= CENTERED_THRESHOLD:
                        print("\n" + "="*60)
                        print("🎯 OBJETO CENTRADO Y CERCA - INICIANDO SECUENCIA DE AGARRE")
                        print("="*60)
                        grab_in_progress = True
                        try:
                            # Secuencia de agarre
                            print("  1. Extendiendo brazo...")
                            robot.mover_codo_tiempo(1, 1.5, velocidad=0.5)
                            time.sleep(0.5)
                            
                            print("  2. Abriendo pinza...")
                            robot.accion_recoger()
                            time.sleep(1.0)
                            
                            print("  3. Levantando...")
                            robot.mover_hombro_tiempo(-1, 0.8, velocidad=0.4)
                            time.sleep(0.5)
                            
                            print("  4. Cerrando pinza...")
                            robot.accion_soltar()
                            time.sleep(1.0)
                            
                            print("  5. Retrayendo...")
                            robot.mover_hombro_tiempo(1, 1.0, velocidad=0.5)
                            time.sleep(0.5)
                            robot.mover_codo_tiempo(-1, 1.5, velocidad=0.5)
                            
                            print("✅ SECUENCIA COMPLETADA")
                            print("="*60 + "\n")
                            
                            # Resetear y pausar auto por 5 segundos
                            object_centered_count = 0
                            time.sleep(5)
                        finally:
                            grab_in_progress = False
                else:
                    # Centrado pero NO cerca
                    object_centered_count = 0
                    print(f"[AUTO] Target: {class_name} CENTRADO pero LEJOS - esperando acercarse más...")
        else:
            # No hay detección o auto desactivado
            object_centered_count = 0
        
        time.sleep(0.01)  # Small delay

def generate_frames():
    """Generar frames para stream CON detecciones dibujadas"""
    while True:
        # Obtener frame original
        with frame_lock:
            if last_frame is None:
                time.sleep(0.1)
                continue
            frame = last_frame.copy()
        
        # Obtener resultados de detección
        with results_lock:
            results = detection_results
        
        # Dibujar detecciones
        if results:
            # Dibujar todas las detecciones
            for det in results['detections']:
                x1, y1, x2, y2 = det['box']
                class_name = det['class']
                conf = det['conf']
                is_target = det['is_target']
                
                # Color: rojo para target, verde para alta confianza, amarillo para baja
                if is_target and results['best'] and results['best'][0] == class_name:
                    color = (0, 0, 255)  # Rojo para el target seleccionado
                elif conf > 0.7:
                    color = (0, 255, 0)  # Verde
                else:
                    color = (0, 255, 255)  # Amarillo
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f'{class_name} {conf:.2f}'
                cv2.putText(frame, label, (x1, y1 - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Dibujar centro y zona muerta
            cv2.circle(frame, (CENTER_X, CENTER_Y), 5, (255, 0, 255), -1)
            cv2.rectangle(frame, 
                        (CENTER_X - DEAD_ZONE_X, CENTER_Y - DEAD_ZONE_Y),
                        (CENTER_X + DEAD_ZONE_X, CENTER_Y + DEAD_ZONE_Y),
                        (255, 0, 255), 1)
            
            # Línea al target si existe
            if results['target_pos']:
                tx, ty = results['target_pos']
                cv2.line(frame, (CENTER_X, CENTER_Y), (tx, ty), (0, 0, 255), 2)
            
            # Status
            status_text = "AUTO: ON" if auto_movement_enabled else "AUTO: OFF"
            status_color = (0, 255, 0) if auto_movement_enabled else (0, 0, 255)
            cv2.putText(frame, status_text, (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Latencia
            cv2.putText(frame, f'Deteccion: {results["latency"]:.0f}ms', (10, 60),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # Target info
            if results['best']:
                cv2.putText(frame, f'Target: {results["best"][0]} ({results["best"][1]:.2f})', 
                          (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Encodear a JPEG con calidad media para velocidad
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Brazo Robótico - Detección en Tiempo Real</title></head>
    <body style="background:#000; color:#fff; font-family:Arial;">
        <h1>🤖 Brazo Robótico - Detección en Tiempo Real</h1>
        <img src="/video_feed" width="100%" style="max-width:1280px;">
        <br><br>
        <button onclick="fetch('/auto_on')" style="padding:20px; font-size:20px; background:green; color:white; border:none; cursor:pointer;">
            ▶ ACTIVAR AUTO
        </button>
        <button onclick="fetch('/auto_off')" style="padding:20px; font-size:20px; background:red; color:white; border:none; cursor:pointer;">
            ⏸ DESACTIVAR AUTO
        </button>
        <button onclick="fetch('/grab')" style="padding:20px; font-size:20px; background:orange; color:white; border:none; cursor:pointer;">
            🤏 AGARRAR
        </button>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/auto_on')
def auto_on():
    global auto_movement_enabled
    auto_movement_enabled = True
    return "AUTO ACTIVADO"

@app.route('/auto_off')
def auto_off():
    global auto_movement_enabled
    auto_movement_enabled = False
    return "AUTO DESACTIVADO"

@app.route('/grab')
def grab():
    robot.mover_codo_tiempo(1, 1.5, velocidad=0.5)
    time.sleep(0.5)
    robot.accion_recoger()
    time.sleep(1.0)
    robot.mover_hombro_tiempo(-1, 0.8, velocidad=0.4)
    time.sleep(0.5)
    robot.accion_soltar()
    time.sleep(1.0)
    robot.mover_hombro_tiempo(1, 1.0, velocidad=0.5)
    time.sleep(0.5)
    robot.mover_codo_tiempo(-1, 1.5, velocidad=0.5)
    return "SECUENCIA COMPLETADA"

if __name__ == '__main__':
    print("="*60)
    print("🤖 BRAZO ROBÓTICO - Sistema de Detección en Tiempo Real")
    print("="*60)
    print("Iniciando threads...")
    
    # Iniciar thread de captura (frames RAW)
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    # Esperar a que haya frames
    time.sleep(2)
    
    # Iniciar thread de detección (YOLO)
    detect_thread = threading.Thread(target=detection_thread, daemon=True)
    detect_thread.start()
    
    print("✓ Stream de cámara activo")
    print("✓ Detección YOLO activa")
    print("✓ MODO AUTOMÁTICO ACTIVADO 🚀")
    print("\n" + "="*60)
    print("ABRE TU NAVEGADOR EN:")
    print("  http://<IP-RASPBERRY>:5000")
    print("="*60)
    print("\nControles web disponibles:")
    print("  ▶ ACTIVAR AUTO   - Reactivar seguimiento")
    print("  ⏸ DESACTIVAR AUTO - Pausar seguimiento")
    print("  🤏 AGARRAR       - Secuencia de agarre manual")
    print("\n⚠️  El brazo se moverá AUTOMÁTICAMENTE al detectar objetos!")
    print("="*60 + "\n")
    
    # Iniciar servidor web
    app.run(host='0.0.0.0', port=5000, threaded=True)
