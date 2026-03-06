#!/usr/bin/env python3
"""
Web Interface for Robot Arm Control
Provides a web-based interface to control the robot arm with sliders and buttons
"""

from flask import Flask, render_template_string, request, jsonify
import time
import logging as log

try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

class ControladorWeb:
    """Controlador web para interfaz del brazo robótico"""

    def __init__(self):
        """Inicializar controlador web"""
        self.controlador_robot = ControladorRobotico()
        self.angulos_actuales = {
            'base': 180,
            'shoulder': 45,
            'elbow': 90,
            'gripper': 0
        }
        self.retardo_movimiento = 0.1  # Retardo entre movimientos
        self.velocidad = 2  # Velocidad más lenta para mejor precisión
        log.info("Controlador web inicializado")

    def movimiento_suave_tiempo(self, articulación, tiempo_segundos, direccion, pasos=10):
        """Movimiento suave basado en tiempo"""
        try:
            tiempo_paso = tiempo_segundos / pasos

            for paso in range(pasos):
                if articulación == 'base':
                    self.controlador_robot.mover_base_tiempo(direccion, tiempo_paso, velocidad=self.velocidad)
                elif articulación == 'shoulder':
                    self.controlador_robot.mover_hombro_tiempo(direccion, tiempo_paso, velocidad=self.velocidad)
                elif articulación == 'elbow':
                    self.controlador_robot.mover_codo_tiempo(direccion, tiempo_paso, velocidad=self.velocidad)
                elif articulación == 'gripper':
                    self.controlador_robot.mover_pinza_tiempo(direccion, tiempo_paso, velocidad=self.velocidad)

                time.sleep(self.retardo_movimiento / pasos)

            return True, f"{articulación.title()} movido suavemente {tiempo_segundos:.1f}s en dirección {direccion}"

        except Exception as e:
            return False, f"Error en movimiento suave {articulación}: {e}"

    def mover_articulación_tiempo(self, articulación, tiempo_segundos, direccion):
        """Mover articulación específica por tiempo con validación"""
        try:
            tiempo_segundos = float(tiempo_segundos)
            direccion = int(direccion)

            # Validar parámetros
            if not (0.1 <= tiempo_segundos <= 5.0):
                return False, f"Tiempo debe estar entre 0.1-5.0 segundos"

            if direccion not in [-1, 1]:
                return False, f"Dirección debe ser -1 o 1"

            # Ejecutar movimiento con límites físicos
            if articulación == 'base':
                tiempo_real = self.controlador_robot.mover_base_tiempo(direccion, tiempo_segundos, velocidad=self.velocidad)
            elif articulación == 'shoulder':
                tiempo_real = self.controlador_robot.mover_hombro_tiempo(direccion, tiempo_segundos, velocidad=self.velocidad)
            elif articulación == 'elbow':
                tiempo_real = self.controlador_robot.mover_codo_tiempo(direccion, tiempo_segundos, velocidad=self.velocidad)
            elif articulación == 'gripper':
                tiempo_real = self.controlador_robot.mover_pinza_tiempo(direccion, tiempo_segundos, velocidad=self.velocidad)
            else:
                return False, f"Articulación {articulación} no válida"

            time.sleep(self.retardo_movimiento)

            direction_name = "positiva" if direccion == 1 else "negativa"
            return True, f"{articulación.title()} movido {tiempo_real:.1f}s en dirección {direction_name}"

        except Exception as e:
            return False, f"Error moviendo {articulación}: {e}"

    def ir_a_home(self):
        """Mover a posición home usando movimientos temporizados"""
        try:
            # Movimientos para regresar a posición home (aproximada)
            movimientos_home = [
                ('base', 1.5, -1),     # Ajuste base izquierda
                ('shoulder', 1.0, -1), # Ajuste hombro abajo
                ('elbow', 1.5, 1),     # Ajuste codo extender
                ('gripper', 0.5, 1)    # Abrir pinza
            ]

            for articulación, tiempo, direccion in movimientos_home:
                éxito, mensaje = self.movimiento_suave_tiempo(articulación, tiempo, direccion, pasos=15)
                if not éxito:
                    return False, mensaje
                time.sleep(0.3)

            # Resetear contadores de tiempo
            self.controlador_robot.resetear_tiempos()
            return True, "Movido suavemente a posición home"
        except Exception as e:
            return False, f"Error yendo a home: {e}"

    def secuencia_prueba(self):
        """Ejecutar secuencia de prueba con movimientos temporizados"""
        try:
            movimientos_prueba = [
                ('base', 0.5, 1),      # Base derecha
                ('shoulder', 0.3, 1),  # Hombro arriba
                ('elbow', 0.4, 1),     # Codo extender
                ('gripper', 0.3, -1),  # Pinza cerrar
                ('base', 0.5, -1),     # Base izquierda
                ('shoulder', 0.3, -1), # Hombro abajo
                ('elbow', 0.4, -1),    # Codo contraer
                ('gripper', 0.3, 1)    # Pinza abrir
            ]

            for articulación, tiempo, direccion in movimientos_prueba:
                éxito, mensaje = self.movimiento_suave_tiempo(articulación, tiempo, direccion, pasos=20)
                if not éxito:
                    return False, mensaje
                time.sleep(0.5)

            # Regresar a home
            self.ir_a_home()
            return True, "Secuencia de prueba con tiempo completada"
        except Exception as e:
            return False, f"Prueba fallida: {e}"

# Instancia global del controlador
controlador = ControladorWeb()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Brazo Robótico</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .controls {
            padding: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        .joint-control {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border: 2px solid #e9ecef;
        }
        .joint-control h3 {
            margin-top: 0;
            color: #495057;
            font-size: 1.4em;
            text-align: center;
        }
        .slider-container {
            margin: 20px 0;
        }
        .slider {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: #ddd;
            outline: none;
            appearance: none;
        }
        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .slider::-moz-range-thumb {
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .angle-display {
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
            margin: 10px 0;
        }
        .buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-success {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
        }
        .btn-warning {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(240, 147, 251, 0.4);
        }
        .status {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
            border-left: 5px solid #28a745;
        }
        .status.error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        .status.success {
            border-left-color: #28a745;
            background: #d4edda;
        }
        .current-angles {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        .angle-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .angle-box h4 {
            margin: 0 0 5px 0;
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
        }
        .angle-box .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #495057;
        }
        @media (max-width: 768px) {
            .controls {
                grid-template-columns: 1fr;
            }
            .current-angles {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Control de Brazo Robótico</h1>
            <p>Interfaz web para control preciso de articulaciones</p>
        </div>

        <div class="controls">
            <!-- Base Control -->
            <div class="joint-control">
                <h3>🔄 Base (Tiempo)</h3>
                    <div class="slider-container">
                        <input type="range" min="0.1" max="5.0" step="0.1" value="0.5" class="slider" id="base-time-slider">
                    </div>
                    <div class="angle-display" id="base-time-display">0.5s</div>
                    <div class="buttons">
                        <button class="btn btn-primary" onclick="moveJoint('base', parseFloat(document.getElementById('base-time-slider').value), -1)">← Izq</button>
                        <button class="btn btn-primary" onclick="moveJoint('base', parseFloat(document.getElementById('base-time-slider').value), 0)">STOP</button>
                        <button class="btn btn-primary" onclick="moveJoint('base', parseFloat(document.getElementById('base-time-slider').value), 1)">Der →</button>
                    </div>
            </div>

            <!-- Shoulder Control -->
            <div class="joint-control">
                <h3>💪 Hombro (Tiempo)</h3>
                <div class="slider-container">
                    <input type="range" min="0.1" max="5.0" step="0.1" value="0.5" class="slider" id="shoulder-time-slider">
                </div>
                <div class="angle-display" id="shoulder-time-display">0.5s</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="moveJoint('shoulder', parseFloat(document.getElementById('shoulder-time-slider').value), 1)">↑ Subir</button>
                    <button class="btn btn-primary" onclick="moveJoint('shoulder', parseFloat(document.getElementById('shoulder-time-slider').value), 0)">STOP</button>
                    <button class="btn btn-primary" onclick="moveJoint('shoulder', parseFloat(document.getElementById('shoulder-time-slider').value), -1)">↓ Bajar</button>
                </div>
            </div>

            <!-- Elbow Control -->
            <div class="joint-control">
                <h3>🦾 Codo (Tiempo)</h3>
                <div class="slider-container">
                    <input type="range" min="0.1" max="5.0" step="0.1" value="0.5" class="slider" id="elbow-time-slider">
                </div>
                <div class="angle-display" id="elbow-time-display">0.5s</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="moveJoint('elbow', parseFloat(document.getElementById('elbow-time-slider').value), 1)">↑ Extender</button>
                    <button class="btn btn-primary" onclick="moveJoint('elbow', parseFloat(document.getElementById('elbow-time-slider').value), 0)">STOP</button>
                    <button class="btn btn-primary" onclick="moveJoint('elbow', parseFloat(document.getElementById('elbow-time-slider').value), -1)">↓ Contraer</button>
                </div>
            </div>

            <!-- Gripper Control -->
            <div class="joint-control">
                <h3>✋ Pinza (Tiempo)</h3>
                <div class="slider-container">
                    <input type="range" min="0.1" max="5.0" step="0.1" value="0.5" class="slider" id="gripper-time-slider">
                </div>
                <div class="angle-display" id="gripper-time-display">0.5s</div>
                <div class="buttons">
                    <button class="btn btn-success" onclick="moveJoint('gripper', parseFloat(document.getElementById('gripper-time-slider').value), 1)">Abrir</button>
                    <button class="btn btn-primary" onclick="moveJoint('gripper', parseFloat(document.getElementById('gripper-time-slider').value), 0)">STOP</button>
                    <button class="btn btn-warning" onclick="moveJoint('gripper', parseFloat(document.getElementById('gripper-time-slider').value), -1)">Cerrar</button>
                </div>
            </div>
        </div>

        <!-- Action Buttons -->
        <div style="padding: 30px; text-align: center;">
            <button class="btn btn-success" style="font-size: 1.2em; padding: 15px 30px; margin: 0 10px;" onclick="goHome()">
                🏠 Ir a Home
            </button>
            <button class="btn btn-warning" style="font-size: 1.2em; padding: 15px 30px; margin: 0 10px;" onclick="testSequence()">
                🧪 Probar Movimientos
            </button>
        </div>

        <!-- Configuración de Movimiento -->
        <div style="padding: 20px; background: #f8f9fa; margin: 20px; border-radius: 10px;">
            <h3 style="text-align: center; color: #495057;">⚙️ Configuración de Movimiento</h3>
            <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                <div>
                    <label style="display: block; margin-bottom: 5px;">Velocidad:</label>
                    <select id="speed-select" onchange="updateSpeed(this.value)">
                        <option value="1">Muy Lenta</option>
                        <option value="2" selected>Lenta</option>
                        <option value="3">Normal</option>
                        <option value="5">Rápida</option>
                    </select>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 5px;">Suavizado:</label>
                    <select id="smooth-select" onchange="updateSmoothing(this.value)">
                        <option value="5">Mínimo</option>
                        <option value="10" selected>Normal</option>
                        <option value="20">Máximo</option>
                    </select>
                </div>
                <button class="btn btn-primary" onclick="emergencyStop()">
                    🚫 Parada de Emergencia
                </button>
            </div>
        </div>

        <!-- Current Times Display -->
        <div class="current-angles">
            <div class="angle-box">
                <h4>Base</h4>
                <div class="value" id="current-base">0.0s</div>
            </div>
            <div class="angle-box">
                <h4>Hombro</h4>
                <div class="value" id="current-shoulder">0.0s</div>
            </div>
            <div class="angle-box">
                <h4>Codo</h4>
                <div class="value" id="current-elbow">0.0s</div>
            </div>
            <div class="angle-box">
                <h4>Pinza</h4>
                <div class="value" id="current-gripper">0.0s</div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="status" class="status" style="display: none;"></div>
    </div>

    <script>
        // Update time displays in real-time for each joint
        function updateTimeDisplay(sliderId, displayId) {
            const slider = document.getElementById(sliderId);
            const display = document.getElementById(displayId);

            slider.addEventListener('input', function() {
                display.textContent = parseFloat(this.value).toFixed(1) + 's';
            });
        }

        updateTimeDisplay('base-time-slider', 'base-time-display');
        updateTimeDisplay('shoulder-time-slider', 'shoulder-time-display');
        updateTimeDisplay('elbow-time-slider', 'elbow-time-display');
        updateTimeDisplay('gripper-time-slider', 'gripper-time-display');

        // Move on slider release (not during drag) - default positive direction
        document.getElementById('base-time-slider').addEventListener('change', function() {
            moveJoint('base', parseFloat(this.value), 1);
        });
        document.getElementById('shoulder-time-slider').addEventListener('change', function() {
            moveJoint('shoulder', parseFloat(this.value), 1);
        });
        document.getElementById('elbow-time-slider').addEventListener('change', function() {
            moveJoint('elbow', parseFloat(this.value), 1);
        });
        document.getElementById('gripper-time-slider').addEventListener('change', function() {
            moveJoint('gripper', parseFloat(this.value), 1);
        });

        // Generic joint mover: sends time (seconds) and direction (-1, 0, 1)
        let lastMoveTime = 0;
        const MOVE_COOLDOWN = 100; // ms

        function moveJoint(joint, timeSeconds, direction) {
            const now = Date.now();
            if (now - lastMoveTime < MOVE_COOLDOWN) return;
            lastMoveTime = now;

            // If direction is 0, perform emergency stop (stop all)
            if (direction === 0) {
                fetch('/emergency_stop', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    showStatus('warning', data.message);
                    if (data.times) updateCurrentTimes(data.times);
                })
                .catch(err => showStatus('error', 'Error de conexión: ' + err));
                return;
            }

            // Update display immediately for UX
            const displayEl = document.getElementById(joint + '-time-display');
            if (displayEl) displayEl.textContent = parseFloat(timeSeconds).toFixed(1) + 's';

            fetch('/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ joint: joint, time: timeSeconds, direction: direction })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success && data.times) {
                    window.updatingFromServer = true;
                    updateCurrentTimes(data.times);
                    window.updatingFromServer = false;
                } else if (!data.success) {
                    // Revert on error
                    fetch('/times')
                    .then(r => r.json())
                    .then(currentTimes => updateCurrentTimes(currentTimes));
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
                fetch('/times')
                .then(r => r.json())
                .then(currentTimes => updateCurrentTimes(currentTimes));
            });
        }

        function goHome() {
            fetch('/home', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success && data.times) updateCurrentTimes(data.times);
            })
            .catch(error => showStatus('error', 'Error de conexión: ' + error));
        }

        function testSequence() {
            fetch('/test', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success && data.times) updateCurrentTimes(data.times);
            })
            .catch(error => showStatus('error', 'Error de conexión: ' + error));
        }

        function updateCurrentTimes(times) {
            if (times && typeof times === 'object') {
                document.getElementById('current-base').textContent = times.base.toFixed(1) + 's';
                document.getElementById('current-shoulder').textContent = times.shoulder.toFixed(1) + 's';
                document.getElementById('current-elbow').textContent = times.elbow.toFixed(1) + 's';
                document.getElementById('current-gripper').textContent = times.gripper.toFixed(1) + 's';

                document.getElementById('base-time-display').textContent = times.base.toFixed(1) + 's';
                document.getElementById('shoulder-time-display').textContent = times.shoulder.toFixed(1) + 's';
                document.getElementById('elbow-time-display').textContent = times.elbow.toFixed(1) + 's';
                document.getElementById('gripper-time-display').textContent = times.gripper.toFixed(1) + 's';
            }
        }

        function showStatus(type, message) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
        }

        window.updatingFromServer = false;

        // Auto-update times to current values (only once at startup)
        setTimeout(() => {
            fetch('/times')
            .then(response => response.json())
            .then(data => { window.updatingFromServer = true; updateCurrentTimes(data); window.updatingFromServer = false; });
        }, 1000);

        // Configuration endpoints
        function updateSpeed(speed) {
            fetch('/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ setting: 'speed', value: parseInt(speed) }) })
            .then(response => response.json()).then(data => showStatus('success', 'Velocidad actualizada: ' + data.value));
        }

        function updateSmoothing(steps) {
            fetch('/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ setting: 'smooth_steps', value: parseInt(steps) }) })
            .then(response => response.json()).then(data => showStatus('success', 'Suavizado actualizado: ' + data.value + ' pasos'));
        }

        function emergencyStop() {
            fetch('/emergency_stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => { showStatus('warning', data.message); if (data.times) updateCurrentTimes(data.times); });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, angles={'base': 0.0, 'shoulder': 0.0, 'elbow': 0.0, 'gripper': 0.0})

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    joint = data.get('joint')
    time_seconds = data.get('time', 0.5)  # Default 0.5 seconds
    direction = data.get('direction', 1)  # Default positive direction

    success, message = controlador.mover_articulación_tiempo(joint, time_seconds, direction)

    return jsonify({
        'success': success,
        'message': message,
        'times': controlador.controlador_robot.obtener_estado_tiempos()
    })

@app.route('/home', methods=['POST'])
def home():
    success, message = controlador.ir_a_home()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controlador.angulos_actuales,
        'times': controlador.controlador_robot.obtener_estado_tiempos()
    })

@app.route('/test', methods=['POST'])
def test():
    success, message = controlador.secuencia_prueba()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controlador.angulos_actuales,
        'times': controlador.controlador_robot.obtener_estado_tiempos()
    })

@app.route('/times')
def get_times():
    return jsonify(controlador.controlador_robot.obtener_estado_tiempos())

@app.route('/config', methods=['POST'])
def config():
    data = request.get_json()
    setting = data.get('setting')
    value = data.get('value')

    if setting == 'speed':
        controlador.velocidad = max(1, min(10, value))
        return jsonify({'success': True, 'value': controlador.velocidad})
    elif setting == 'smooth_steps':
        controlador.pasos_suavizado = max(5, min(30, value))
        return jsonify({'success': True, 'value': controlador.pasos_suavizado})

    return jsonify({'success': False, 'message': 'Configuración no válida'})

@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    """Detener todos los movimientos inmediatamente"""
    try:
        # Detener todos los servos
        controlador.controlador_robot.controlador_servo.detener_todos()

        # Resetear contadores de tiempo
        controlador.controlador_robot.resetear_tiempos()

        return jsonify({
            'success': True,
            'message': 'Parada de emergencia ejecutada - todos los servos detenidos',
            'times': controlador.controlador_robot.obtener_estado_tiempos()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en parada de emergencia: {e}'
        })

if __name__ == '__main__':
    print("🤖 Iniciando servidor web en http://localhost:5000")
    print("Asegúrate de que la alimentación del brazo esté CONECTADA")
    app.run(host='0.0.0.0', port=5000, debug=False)