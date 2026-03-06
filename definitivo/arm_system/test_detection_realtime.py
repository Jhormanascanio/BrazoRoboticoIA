#!/usr/bin/env python3
"""
Detección de objetos en tiempo real con control automático del brazo
Compatible con Raspberry Pi y cámara libcamera
"""
import cv2
import time
import subprocess
import numpy as np
from ultralytics import YOLO
from control.robot_controller import ControladorRobotico

# Cargar el modelo YOLO
print("Cargando modelo YOLO...")
# Usar yolo11n (más rápido) en lugar de yolo11s
model = YOLO("perception/vision/detection/models/torch/yolo11n.pt")
print("Modelo cargado. Optimizando para Raspberry Pi...")

# Inicializar controlador del brazo
print("Inicializando controlador del brazo...")
robot = ControladorRobotico()

# Configuración de la cámara (reducir resolución para mejor FPS)
WIDTH = 640  # Reducido de 1280
HEIGHT = 480  # Reducido de 720
FPS = 30

# Configuración de detección y movimiento
CONFIDENCE_THRESHOLD = 0.55
TARGET_CLASSES = ['bottle', 'cup', 'cell phone', 'book']  # Objetos de interés
DETECTION_SKIP_FRAMES = 2  # Detectar cada 2 frames (optimización)

# Centro de la imagen y zona muerta
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2
DEAD_ZONE_X = 100  # píxeles
DEAD_ZONE_Y = 80

# Variables de control
last_movement_time = 0
MOVEMENT_COOLDOWN = 0.3  # Reducido para seguimiento más fluido
CENTERED_TIME_REQUIRED = 2.0  # Segundos centrado antes de agarrar
centered_start_time = None
last_target_pos = None
STABILITY_THRESHOLD = 20  # Píxeles de movimiento permitido para considerar "quieto"
detection_frame_counter = 0  # Para saltar frames
last_detection_results = None  # Cache de última detección

print("Iniciando stream de cámara con rpicam-vid...")

# Comando rpicam-vid que envía video por stdout
cmd = [
    'rpicam-vid',
    '--inline',           # Headers en cada frame
    '--codec', 'mjpeg',   # Codec MJPEG para fácil decode
    '--width', str(WIDTH),
    '--height', str(HEIGHT),
    '--framerate', str(FPS),
    '-t', '0',            # Sin timeout (continuo)
    '-o', '-',            # Output a stdout
    '--nopreview',        # Sin preview
    '--rotation', '180'   # Rotar 180° (tu flip)
]

# Iniciar el proceso de rpicam-vid
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    bufsize=10**8  # Buffer grande para mejor rendimiento
)

print("Stream iniciado. CONTROLES:")
print("  'a' = Activar/Desactivar seguimiento automático")
print("  'g' = Ejecutar secuencia de agarre manual")
print("  'h' = Detener motores (HOME)")
print("  'q' = Salir")
print("  Flechas: Control manual (←→ base, ↑↓ hombro)")
print("Optimizaciones activas: Resolución 640x480, YOLO11n, Skip frames")
print("-" * 60)

# Buffer para acumular datos JPEG
jpeg_buffer = b''
frame_count = 0
start_time_total = time.time()

# Control de movimiento automático
auto_movement_enabled = False

def calculate_movement(obj_x, obj_y):
    """Calcular movimiento necesario para centrar el objeto
    
    Configuración del brazo:
    - Motor paso a paso: Gira horizontalmente (izquierda/derecha)
    - Servos 1,2,3: Movimiento vertical (arriba/abajo)
    - Cámara: En la pinza, mirando hacia adelante
    
    Lógica:
    - Si objeto está a la DERECHA en imagen → girar motor paso a paso a la DERECHA
    - Si objeto está a la IZQUIERDA en imagen → girar motor paso a paso a la IZQUIERDA
    - Si objeto está ARRIBA en imagen → bajar servos (más cerca del suelo)
    - Si objeto está ABAJO en imagen → subir servos (más alto)
    """
    # Calcular error de posición
    error_x = obj_x - CENTER_X
    error_y = obj_y - CENTER_Y
    
    # Aplicar zona muerta
    if abs(error_x) < DEAD_ZONE_X:
        error_x = 0
    if abs(error_y) < DEAD_ZONE_Y:
        error_y = 0
    
    # Si el objeto está centrado, retornar None
    if error_x == 0 and error_y == 0:
        return None
    
    # Calcular tiempo de movimiento proporcional al error
    # Tiempos más cortos para movimientos más precisos
    time_horizontal = max(0.2, min(abs(error_x) / WIDTH * 1.0, 1.0))
    time_vertical = max(0.2, min(abs(error_y) / HEIGHT * 1.0, 1.0))
    
    # Determinar dirección CORRECTA:
    # Horizontal (motor paso a paso): si error_x > 0, objeto está a la derecha, girar derecha (1)
    dir_horizontal = 1 if error_x > 0 else -1
    
    # Vertical (servos): si error_y > 0, objeto está abajo, subir brazo (1)
    # si error_y < 0, objeto está arriba, bajar brazo (-1)
    dir_vertical = 1 if error_y > 0 else -1
    
    return {
        'horizontal': (dir_horizontal, time_horizontal) if error_x != 0 else None,
        'vertical': (dir_vertical, time_vertical) if error_y != 0 else None
    }

def move_to_object(movement):
    """Mover el brazo hacia el objeto detectado
    
    - Movimiento horizontal: usa motor paso a paso (giro horizontal)
    - Movimiento vertical: usa servos 1,2,3 (hombro principalmente para vertical)
    """
    global last_movement_time
    
    if movement is None:
        return True  # Centrado
    
    current_time = time.time()
    if current_time - last_movement_time < MOVEMENT_COOLDOWN:
        return False  # Cooldown activo
    
    # Mover horizontalmente con motor paso a paso
    if movement['horizontal']:
        direction, duration = movement['horizontal']
        # Convertir duración a distancia aproximada en mm
        distance_mm = int(duration * 30)  # ~30mm por segundo (ajustable)
        print(f"⟲ Girando horizontal: dir={direction}, dist={distance_mm}mm")
        robot.mover_brazo(distance_mm, direccion=direction, velocidad=800)  # Parámetros correctos
        time.sleep(0.1)
    
    # Mover verticalmente con servos (hombro)
    if movement['vertical']:
        direction, duration = movement['vertical']
        print(f"↕ Moviendo vertical: dir={direction}, tiempo={duration:.2f}s")
        robot.mover_hombro_tiempo(direction, duration, velocidad=0.4)
        time.sleep(0.1)
    
    last_movement_time = current_time
    return False

def grab_object():
    """Secuencia para agarrar objeto"""
    print("\n" + "="*60)
    print("¡OBJETO CENTRADO Y ESTABLE! Iniciando secuencia de agarre...")
    print("="*60)
    
    # Extender codo hacia adelante
    print("1. Extendiendo codo...")
    robot.mover_codo_tiempo(1, 1.5, velocidad=0.5)
    time.sleep(0.5)
    
    # Abrir pinza
    print("2. Abriendo pinza...")
    robot.accion_recoger()
    time.sleep(1.0)
    
    # Bajar un poco más (ajustar según altura del objeto)
    print("3. Bajando para agarrar...")
    robot.mover_hombro_tiempo(-1, 0.8, velocidad=0.4)
    time.sleep(0.5)
    
    # Cerrar pinza para agarrar
    print("4. Cerrando pinza - ¡AGARRANDO!")
    robot.accion_soltar()
    time.sleep(1.0)
    
    # Levantar objeto
    print("5. Levantando objeto...")
    robot.mover_hombro_tiempo(1, 1.0, velocidad=0.5)
    time.sleep(0.5)
    
    # Retraer codo
    print("6. Retrayendo codo...")
    robot.mover_codo_tiempo(-1, 1.5, velocidad=0.5)
    time.sleep(0.5)
    
    print("¡Secuencia completada!")
    print("="*60 + "\n")
    
    return True

try:
    while True:
        # Leer chunk de datos
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        
        jpeg_buffer += chunk
        
        # Buscar inicio de JPEG (0xFFD8) y fin (0xFFD9)
        start_marker = jpeg_buffer.find(b'\xff\xd8')
        end_marker = jpeg_buffer.find(b'\xff\xd9')
        
        # Si encontramos un frame completo
        if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
            # Extraer el JPEG completo
            jpeg_data = jpeg_buffer[start_marker:end_marker+2]
            jpeg_buffer = jpeg_buffer[end_marker+2:]  # Limpiar buffer
            
            # Decodificar JPEG a numpy array
            frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if frame is not None:
                frame_count += 1
                detection_frame_counter += 1
                
                # Solo detectar cada N frames para mejorar FPS
                should_detect = (detection_frame_counter % DETECTION_SKIP_FRAMES == 0)
                
                # Variables para tracking del mejor objeto
                best_detection = None
                best_confidence = 0
                target_center_x = None
                target_center_y = None
                boxes_obj = None
                
                if should_detect:
                    # Medir tiempo de detección
                    start_time = time.time()
                    
                    # Realizar detección
                    results = model(frame, conf=0.55, verbose=False, imgsz=640)  # imgsz para optimizar
                    
                    # Calcular latencia
                    latency = (time.time() - start_time) * 1000
                    
                    # Procesar resultados
                    boxes_obj = results[0].boxes
                    last_detection_results = (boxes_obj, latency)
                else:
                    # Usar última detección para mostrar
                    if last_detection_results:
                        boxes_obj, latency = last_detection_results
                    else:
                        latency = 0
                
                if boxes_obj is not None and len(boxes_obj) > 0:
                    bboxes = boxes_obj.xyxy.cpu().numpy()
                    confs = boxes_obj.conf.cpu().numpy()
                    classes = boxes_obj.cls.cpu().numpy()
                    
                    # Dibujar todas las detecciones y encontrar mejor target
                    for i, box in enumerate(bboxes):
                        x1, y1, x2, y2 = map(int, box)
                        class_name = model.names[int(classes[i])]
                        label = f'{class_name} {confs[i]:.2f}'
                        
                        # Color según confianza
                        color = (0, 255, 0) if confs[i] > 0.7 else (0, 255, 255)
                        
                        # Si es un objeto de interés y tiene mejor confianza
                        if class_name in TARGET_CLASSES and confs[i] > best_confidence:
                            best_detection = (class_name, confs[i], box)
                            best_confidence = confs[i]
                            target_center_x = (x1 + x2) // 2
                            target_center_y = (y1 + y2) // 2
                            color = (0, 0, 255)  # Rojo para target seleccionado
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, label, (x1, y1 - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Dibujar centro de pantalla y zona muerta
                cv2.circle(frame, (CENTER_X, CENTER_Y), 5, (255, 0, 255), -1)
                cv2.rectangle(frame, 
                            (CENTER_X - DEAD_ZONE_X, CENTER_Y - DEAD_ZONE_Y),
                            (CENTER_X + DEAD_ZONE_X, CENTER_Y + DEAD_ZONE_Y),
                            (255, 0, 255), 1)
                
                # Si hay un target y movimiento automático está activado
                if best_detection and auto_movement_enabled and target_center_x:
                    class_name, conf, box = best_detection
                    
                    # Dibujar línea del centro al target
                    cv2.line(frame, (CENTER_X, CENTER_Y), 
                           (target_center_x, target_center_y), (0, 0, 255), 2)
                    
                    # Calcular y ejecutar movimiento
                    movement = calculate_movement(target_center_x, target_center_y)
                    
                    # Verificar si está centrado
                    is_centered = (movement is None)
                    
                    # Verificar estabilidad (si el objeto no se mueve mucho)
                    is_stable = False
                    if last_target_pos:
                        distance = np.sqrt((target_center_x - last_target_pos[0])**2 + 
                                         (target_center_y - last_target_pos[1])**2)
                        is_stable = distance < STABILITY_THRESHOLD
                    
                    last_target_pos = (target_center_x, target_center_y)
                    
                    if is_centered and is_stable:
                        # Objeto centrado y estable
                        if centered_start_time is None:
                            centered_start_time = time.time()
                            print("\n¡Objeto centrado! Esperando estabilidad...")
                        
                        time_centered = time.time() - centered_start_time
                        
                        # Mostrar progreso
                        progress = int((time_centered / CENTERED_TIME_REQUIRED) * 100)
                        cv2.putText(frame, f"CENTRADO: {progress}%", 
                                  (CENTER_X - 100, CENTER_Y - 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                        
                        # Barra de progreso
                        bar_width = 200
                        bar_height = 20
                        bar_x = CENTER_X - bar_width // 2
                        bar_y = CENTER_Y - 20
                        cv2.rectangle(frame, (bar_x, bar_y), 
                                    (bar_x + bar_width, bar_y + bar_height), 
                                    (255, 255, 255), 2)
                        fill_width = int((progress / 100) * bar_width)
                        cv2.rectangle(frame, (bar_x, bar_y), 
                                    (bar_x + fill_width, bar_y + bar_height), 
                                    (0, 255, 0), -1)
                        
                        # Si ha estado centrado suficiente tiempo, agarrar
                        if time_centered >= CENTERED_TIME_REQUIRED:
                            grab_object()
                            centered_start_time = None
                            auto_movement_enabled = False  # Desactivar después de agarrar
                            print("\nMovimiento automático DESACTIVADO. Presiona SPACE para reactivar.")
                    
                    else:
                        # No está centrado o no es estable, resetear timer
                        centered_start_time = None
                        
                        # Mover hacia el objeto
                        if movement:
                            centered = move_to_object(movement)
                
                else:
                    # No hay target, resetear tracking
                    centered_start_time = None
                    last_target_pos = None
                
                # Calcular FPS real
                elapsed = time.time() - start_time_total
                fps_real = frame_count / elapsed if elapsed > 0 else 0
                
                # Mostrar información en pantalla
                status_text = "AUTO: ON" if auto_movement_enabled else "AUTO: OFF"
                status_color = (0, 255, 0) if auto_movement_enabled else (0, 0, 255)
                
                cv2.putText(frame, f'Latency: {latency:.1f}ms | FPS: {fps_real:.1f}',
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, status_text, (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
                
                if best_detection:
                    cv2.putText(frame, f'Target: {best_detection[0]}', (10, 90),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Mostrar frame
                cv2.imshow("YOLO Deteccion en Tiempo Real - Raspberry Pi", frame)
                
                # Manejo de teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('a'):  # A para toggle auto movement
                    auto_movement_enabled = not auto_movement_enabled
                    centered_start_time = None  # Reset timer
                    print(f"\nMovimiento automático: {'ACTIVADO ✓' if auto_movement_enabled else 'DESACTIVADO ✗'}")
                elif key == ord('g'):  # G para grab manual
                    print("\nEjecutando secuencia de agarre manual...")
                    grab_object()
                elif key == ord('h'):  # H para home/stop
                    print("\nDeteniendo motores...")
                    robot.mover_hombro_tiempo(0, 0.1, velocidad=0.5)
                    print("Motores detenidos")
                # Control manual con flechas
                elif key == 81:  # Flecha izquierda - motor paso a paso izquierda
                    print("← Girando izquierda (paso a paso)")
                    robot.mover_brazo(30, direccion=-1, velocidad=800)
                elif key == 83:  # Flecha derecha - motor paso a paso derecha
                    print("→ Girando derecha (paso a paso)")
                    robot.mover_brazo(30, direccion=1, velocidad=800)
                elif key == 82:  # Flecha arriba - servos arriba
                    print("↑ Subiendo (servos)")
                    robot.mover_hombro_tiempo(1, 0.5, velocidad=0.5)
                elif key == 84:  # Flecha abajo - servos abajo
                    print("↓ Bajando (servos)")
                    robot.mover_hombro_tiempo(-1, 0.5, velocidad=0.5)

except KeyboardInterrupt:
    print("\nInterrumpido por usuario")

finally:
    # Detener motores
    print("\nDeteniendo motores...")
    try:
        robot.mover_hombro_tiempo(0, 0.1, velocidad=0.5)
        robot.cerrar()
    except:
        pass
    
    # Limpiar
    process.terminate()
    process.wait()
    cv2.destroyAllWindows()
    
    # Estadísticas finales
    elapsed = time.time() - start_time_total
    print(f"\nEstadísticas:")
    print(f"  Frames procesados: {frame_count}")
    print(f"  Tiempo total: {elapsed:.2f}s")
    print(f"  FPS promedio: {frame_count/elapsed:.2f}")
    print("\n¡Sistema cerrado correctamente!")
