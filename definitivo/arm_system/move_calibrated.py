#!/usr/bin/env python3
"""
Move Robot Arm with Calibrated Angles
Uses the angles registered in manual_control.py to move the physical arm
"""

import time
import logging as log
try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    # Fallback for Windows testing
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class CalibratedMover:
    def __init__(self):
        self.controlador_robot = ControladorRobotico()
        # Tiempos calibrados basados en movimientos temporizados
        # Estos valores representan el tiempo necesario para alcanzar posiciones calibradas
        self.calibrated_times = {
            'base': {'derecha': 1.2, 'izquierda': 1.2},      # Tiempo para movimientos de base
            'shoulder': {'arriba': 0.8, 'abajo': 0.8},       # Tiempo para movimientos de hombro
            'elbow': {'extender': 1.5, 'contraer': 1.5},     # Tiempo para movimientos de codo
            'gripper': {'abrir': 0.5, 'cerrar': 0.5}         # Tiempo para movimientos de pinza
        }
        log.info("Calibrated Mover initialized")

    def run(self):
        """Main calibrated movement interface"""
        print("\n" + "="*50)
        print("🤖 MOVIMIENTO CON TIEMPOS CALIBRADOS")
        print("="*50)
        print("INSTRUCCIONES:")
        print("1. Asegúrate de que la alimentación esté CONECTADA")
        print("2. Los movimientos están LIMITADOS por seguridad física")
        print("3. Usa tiempos calibrados para movimientos precisos")
        print("\nComandos:")
        print("  b+<seg> - Base derecha (ej: b+1.2)")
        print("  b-<seg> - Base izquierda (ej: b-1.2)")
        print("  s+<seg> - Hombro arriba (ej: s+0.8)")
        print("  s-<seg> - Hombro abajo (ej: s-0.8)")
        print("  e+<seg> - Codo extender (ej: e+1.5)")
        print("  e-<seg> - Codo contraer (ej: e-1.5)")
        print("  g+<seg> - Pinza abrir (ej: g+0.5)")
        print("  g-<seg> - Pinza cerrar (ej: g-0.5)")
        print("  home     - Ir a posición calibrada")
        print("  test     - Probar movimientos calibrados")
        print("  q        - Salir")
        print("\nEjemplo de uso:")
        print("  b+1.2    - Base derecha 1.2 segundos")
        print("  s+0.8    - Hombro arriba 0.8 segundos")
        print("  home     - Posición calibrada completa")
        print("="*50)

        while True:
            try:
                cmd = input("\nmover> ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'home':
                    self.go_to_calibrated_position()
                elif cmd == 'test':
                    self.test_movements()
                elif cmd.startswith(('b', 's', 'e', 'g')):
                    self.move_with_time(cmd)
                else:
                    print("❌ Usa: b<ángulo>, s<ángulo>, e<ángulo>, g<ángulo>, home, test, q")

            except KeyboardInterrupt:
                print("\n👋 Saliendo del movimiento calibrado...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        self.cleanup()

    def move_with_time(self, cmd):
        """Move specific joint with calibrated time"""
        try:
            if len(cmd) < 3 or cmd[1] not in ['+', '-']:
                print("❌ Formato inválido. Usa: b+1.2, s-0.8, e+1.5, g-0.5")
                return

            joint_letter = cmd[0]
            direction = 1 if cmd[1] == '+' else -1
            time_str = cmd[2:]

            try:
                tiempo_solicitado = float(time_str)
            except ValueError:
                print("❌ Tiempo debe ser un número decimal")
                return

            # Mapear comandos a articulaciones y tiempos calibrados
            joint_map = {
                'b': ('base', 'Base', self.controlador_robot.mover_base_tiempo,
                      'derecha' if direction == 1 else 'izquierda'),
                's': ('shoulder', 'Hombro', self.controlador_robot.mover_hombro_tiempo,
                      'arriba' if direction == 1 else 'abajo'),
                'e': ('elbow', 'Codo', self.controlador_robot.mover_codo_tiempo,
                      'extender' if direction == 1 else 'contraer'),
                'g': ('gripper', 'Pinza', self.controlador_robot.mover_pinza_tiempo,
                      'abrir' if direction == 1 else 'cerrar')
            }

            if joint_letter not in joint_map:
                print("❌ Articulación inválida. Usa: b (base), s (hombro), e (codo), g (pinza)")
                return

            joint, display_name, move_function, direction_name = joint_map[joint_letter]

            # Usar tiempo calibrado si está disponible, sino el solicitado
            tiempo_calibrado = self.calibrated_times[joint][direction_name]
            tiempo_a_usar = min(tiempo_solicitado, tiempo_calibrado)

            print(f"🔄 Moviendo {display_name} {direction_name} {tiempo_a_usar:.1f}s (calibrado: {tiempo_calibrado:.1f}s)...")

            # Ejecutar movimiento
            tiempo_real = move_function(direction, tiempo_a_usar, velocidad=1.0)

            print(f"✅ {display_name} movido {direction_name} {tiempo_real:.1f}s")

        except Exception as e:
            print(f"❌ Error de movimiento: {e}")

    def go_to_calibrated_position(self):
        """Move to calibrated home position using time-based movements"""
        print("🏠 Yendo a posición calibrada...")
        try:
            # Secuencia de movimientos para alcanzar posición home calibrada
            # Base: ajustar a posición central
            self.controlador_robot.mover_base_tiempo(-1, self.calibrated_times['base']['izquierda'] * 0.5, velocidad=1.0)
            time.sleep(0.3)

            # Hombro: posición media
            self.controlador_robot.mover_hombro_tiempo(-1, self.calibrated_times['shoulder']['abajo'] * 0.3, velocidad=1.0)
            time.sleep(0.3)

            # Codo: posición extendida media
            self.controlador_robot.mover_codo_tiempo(1, self.calibrated_times['elbow']['extender'] * 0.4, velocidad=1.0)
            time.sleep(0.3)

            # Pinza: abierta
            self.controlador_robot.mover_pinza_tiempo(1, self.calibrated_times['gripper']['abrir'], velocidad=1.0)

            print("✅ Posición calibrada alcanzada")
        except Exception as e:
            print(f"❌ Error yendo a posición calibrada: {e}")

    def test_movements(self):
        """Test calibrated movements with time-based controls"""
        print("🧪 Probando movimientos calibrados con tiempos...")

        try:
            # Test base
            print("Probando base...")
            self.controlador_robot.mover_base_tiempo(1, 0.5, velocidad=1.0)   # Derecha
            time.sleep(0.3)
            self.controlador_robot.mover_base_tiempo(-1, 0.5, velocidad=1.0)  # Izquierda
            time.sleep(0.3)

            # Test shoulder
            print("Probando hombro...")
            self.controlador_robot.mover_hombro_tiempo(1, 0.3, velocidad=1.0)  # Arriba
            time.sleep(0.3)
            self.controlador_robot.mover_hombro_tiempo(-1, 0.3, velocidad=1.0) # Abajo
            time.sleep(0.3)

            # Test elbow
            print("Probando codo...")
            self.controlador_robot.mover_codo_tiempo(1, 0.4, velocidad=1.0)   # Extender
            time.sleep(0.3)
            self.controlador_robot.mover_codo_tiempo(-1, 0.4, velocidad=1.0)  # Contraer
            time.sleep(0.3)

            # Test gripper
            print("Probando pinza...")
            self.controlador_robot.mover_pinza_tiempo(-1, 0.3, velocidad=1.0) # Cerrar
            time.sleep(0.3)
            self.controlador_robot.mover_pinza_tiempo(1, 0.3, velocidad=1.0)  # Abrir

            print("✅ Prueba de movimientos calibrados completada")

        except Exception as e:
            print(f"❌ Error en prueba: {e}")

    def cleanup(self):
        """Clean shutdown"""
        print("🔌 Apagando...")
        try:
            self.controlador_robot.cerrar()
            print("✅ Movimiento calibrado cerrado")
        except Exception as e:
            print(f"❌ Error durante apagado: {e}")


if __name__ == '__main__':
    mover = CalibratedMover()
    mover.run()