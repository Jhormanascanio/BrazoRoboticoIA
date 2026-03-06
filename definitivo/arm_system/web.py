#!/usr/bin/env python3
"""
Web Interface for Robot Arm Control
Provides a web-based interface to control the robot arm with sliders and buttons
"""

from flask import Flask, render_template_string, request, jsonify
import time
import logging as log

try:
    from .control.robot_controller import RobotController
except ImportError:
    from control.robot_controller import RobotController

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

class WebController:
    def __init__(self):
        self.robot_controller = RobotController()
        self.current_angles = {
            'base': 180,
            'shoulder': 45,
            'elbow': 90,
            'gripper': 0
        }
        log.info("Web Controller initialized")

    def move_joint(self, joint, angle):
        """Move a specific joint to angle"""
        try:
            angle = int(angle)

            # Validate ranges - all servos configured for 360°
            if not (0 <= angle <= 360):
                return False, f"{joint.title()} angle must be 0-360°"

            # Move joint
            if joint == 'base':
                self.robot_controller.move_base(angle, speed=3)
            elif joint == 'shoulder':
                self.robot_controller.move_shoulder(angle, speed=3)
            elif joint == 'elbow':
                self.robot_controller.move_elbow(angle, speed=3)
            elif joint == 'gripper':
                self.robot_controller.move_gripper(angle, speed=3)

            self.current_angles[joint] = angle
            return True, f"{joint.title()} moved to {angle}°"

        except Exception as e:
            return False, f"Error moving {joint}: {e}"

    def go_home(self):
        """Move to home position"""
        try:
            self.robot_controller.move_base(180, speed=3)
            time.sleep(0.5)
            self.robot_controller.move_shoulder(45, speed=3)
            time.sleep(0.5)
            self.robot_controller.move_elbow(90, speed=3)
            time.sleep(0.5)
            self.robot_controller.move_gripper(0, speed=3)

            self.current_angles = {'base': 180, 'shoulder': 45, 'elbow': 90, 'gripper': 0}
            return True, "Moved to home position"
        except Exception as e:
            return False, f"Error going home: {e}"

    def test_sequence(self):
        """Run test sequence"""
        try:
            # Test each joint
            for joint, angle in [('base', 90), ('shoulder', 60), ('elbow', 120), ('gripper', 90)]:
                success, msg = self.move_joint(joint, angle)
                if not success:
                    return False, msg
                time.sleep(0.5)

            # Return to home
            self.go_home()
            return True, "Test sequence completed"
        except Exception as e:
            return False, f"Test failed: {e}"

# Global controller instance
controller = WebController()

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
                <h3>🔄 Base (0-360°)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="{{ angles.base }}" class="slider" id="base-slider">
                </div>
                <div class="angle-display" id="base-angle">{{ angles.base }}°</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('base', 0)">0°</button>
                    <button class="btn btn-primary" onclick="setAngle('base', 180)">180°</button>
                </div>
            </div>

            <!-- Shoulder Control -->
            <div class="joint-control">
                <h3>💪 Hombro (0-360°)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="{{ angles.shoulder }}" class="slider" id="shoulder-slider">
                </div>
                <div class="angle-display" id="shoulder-angle">{{ angles.shoulder }}°</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('shoulder', 0)">0°</button>
                    <button class="btn btn-primary" onclick="setAngle('shoulder', 90)">90°</button>
                </div>
            </div>

            <!-- Elbow Control -->
            <div class="joint-control">
                <h3>🦾 Codo (0-360°)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="{{ angles.elbow }}" class="slider" id="elbow-slider">
                </div>
                <div class="angle-display" id="elbow-angle">{{ angles.elbow }}°</div>
                <div class="buttons">
                    <button class="btn btn-primary" onclick="setAngle('elbow', 45)">45°</button>
                    <button class="btn btn-primary" onclick="setAngle('elbow', 135)">135°</button>
                </div>
            </div>

            <!-- Gripper Control -->
            <div class="joint-control">
                <h3>✋ Pinza (0-360°)</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="360" value="{{ angles.gripper }}" class="slider" id="gripper-slider">
                </div>
                <div class="angle-display" id="gripper-angle">{{ angles.gripper }}°</div>
                <div class="buttons">
                    <button class="btn btn-success" onclick="setAngle('gripper', 0)">Abrir</button>
                    <button class="btn btn-warning" onclick="setAngle('gripper', 90)">Cerrar</button>
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

        <!-- Current Angles Display -->
        <div class="current-angles">
            <div class="angle-box">
                <h4>Base</h4>
                <div class="value" id="current-base">{{ angles.base }}°</div>
            </div>
            <div class="angle-box">
                <h4>Hombro</h4>
                <div class="value" id="current-shoulder">{{ angles.shoulder }}°</div>
            </div>
            <div class="angle-box">
                <h4>Codo</h4>
                <div class="value" id="current-elbow">{{ angles.elbow }}°</div>
            </div>
            <div class="angle-box">
                <h4>Pinza</h4>
                <div class="value" id="current-gripper">{{ angles.gripper }}°</div>
            </div>
        </div>

        <!-- Status Messages -->
        <div id="status" class="status" style="display: none;"></div>
    </div>

    <script>
        // Update angle displays in real-time
        document.getElementById('base-slider').addEventListener('input', function() {
            document.getElementById('base-angle').textContent = this.value + '°';
        });
        document.getElementById('shoulder-slider').addEventListener('input', function() {
            document.getElementById('shoulder-angle').textContent = this.value + '°';
        });
        document.getElementById('elbow-slider').addEventListener('input', function() {
            document.getElementById('elbow-angle').textContent = this.value + '°';
        });
        document.getElementById('gripper-slider').addEventListener('input', function() {
            document.getElementById('gripper-angle').textContent = this.value + '°';
        });

        // Move on slider release (not during drag)
        document.getElementById('base-slider').addEventListener('change', function() {
            setAngle('base', this.value);
        });
        document.getElementById('shoulder-slider').addEventListener('change', function() {
            setAngle('shoulder', this.value);
        });
        document.getElementById('elbow-slider').addEventListener('change', function() {
            setAngle('elbow', this.value);
        });
        document.getElementById('gripper-slider').addEventListener('change', function() {
            setAngle('gripper', this.value);
        });

        function setAngle(joint, angle) {
            // Update display immediately for smooth UX
            updateAngleDisplay(joint, angle);

            fetch('/move', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ joint: joint, angle: angle })
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    // Only update server values after successful move
                    window.updatingFromServer = true;
                    updateCurrentAngles(data.angles);
                    window.updatingFromServer = false;
                } else {
                    // Revert on error
                    fetch('/angles')
                    .then(response => response.json())
                    .then(currentAngles => {
                        window.updatingFromServer = true;
                        updateCurrentAngles(currentAngles);
                        window.updatingFromServer = false;
                    });
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
                // Revert on error
                fetch('/angles')
                .then(response => response.json())
                .then(currentAngles => {
                    window.updatingFromServer = true;
                    updateCurrentAngles(currentAngles);
                    window.updatingFromServer = false;
                });
            });
        }

        function updateAngleDisplay(joint, angle) {
            // Update the display immediately when slider moves
            const displayId = joint + '-angle';
            const displayElement = document.getElementById(displayId);
            if (displayElement) {
                displayElement.textContent = angle + '°';
            }
        }

        function goHome() {
            fetch('/home', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updateCurrentAngles(data.angles);
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
            });
        }

        function testSequence() {
            fetch('/test', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updateCurrentAngles(data.angles);
                }
            })
            .catch(error => {
                showStatus('error', 'Error de conexión: ' + error);
            });
        }

        function updateCurrentAngles(angles) {
            // Only update if we have valid angles
            if (angles && typeof angles === 'object') {
                document.getElementById('current-base').textContent = angles.base + '°';
                document.getElementById('current-shoulder').textContent = angles.shoulder + '°';
                document.getElementById('current-elbow').textContent = angles.elbow + '°';
                document.getElementById('current-gripper').textContent = angles.gripper + '°';

                // Update sliders ONLY when explicitly requested (not during drag)
                // This prevents sliders from jumping around while user is adjusting
                if (window.updatingFromServer) {
                    document.getElementById('base-slider').value = angles.base;
                    document.getElementById('shoulder-slider').value = angles.shoulder;
                    document.getElementById('elbow-slider').value = angles.elbow;
                    document.getElementById('gripper-slider').value = angles.gripper;

                    // Update angle displays
                    document.getElementById('base-angle').textContent = angles.base + '°';
                    document.getElementById('shoulder-angle').textContent = angles.shoulder + '°';
                    document.getElementById('elbow-angle').textContent = angles.elbow + '°';
                    document.getElementById('gripper-angle').textContent = angles.gripper + '°';
                }
            }
        }

        function showStatus(type, message) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';

            // Hide after 3 seconds
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }

        // Initialize updating flag
        window.updatingFromServer = false;

        // Auto-update sliders to current values (only once at startup)
        setTimeout(() => {
            fetch('/angles')
            .then(response => response.json())
            .then(data => {
                window.updatingFromServer = true;
                updateCurrentAngles(data);
                window.updatingFromServer = false;
            });
        }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, angles=controller.current_angles)

@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    joint = data.get('joint')
    angle = data.get('angle')

    success, message = controller.move_joint(joint, angle)

    return jsonify({
        'success': success,
        'message': message,
        'angles': controller.current_angles
    })

@app.route('/home', methods=['POST'])
def home():
    success, message = controller.go_home()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controller.current_angles
    })

@app.route('/test', methods=['POST'])
def test():
    success, message = controller.test_sequence()
    return jsonify({
        'success': success,
        'message': message,
        'angles': controller.current_angles
    })

@app.route('/angles')
def get_angles():
    return jsonify(controller.current_angles)

if __name__ == '__main__':
    print("🤖 Iniciando servidor web en http://localhost:5000")
    print("Asegúrate de que la alimentación del brazo esté CONECTADA")
    app.run(host='0.0.0.0', port=5000, debug=False)