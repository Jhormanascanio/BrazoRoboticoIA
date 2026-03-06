#!/usr/bin/env python3
"""
Manual Control Interface for Robot Arm
Control individual joints with simple commands
"""

import time
import logging as log
try:
    from .control.robot_controller import ControladorRobotico
except ImportError:
    # Fallback for Windows testing
    from control.robot_controller import ControladorRobotico

log.basicConfig(level=log.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ManualController:
    def __init__(self):
        self.controlador_robot = ControladorRobotico()
        # Estado actual de cada articulación (ahora basado en tiempo acumulado)
        self.current_times = {
            'base': 0.0,      # Tiempo acumulado base
            'shoulder': 0.0,   # Tiempo acumulado hombro
            'elbow': 0.0,      # Tiempo acumulado codo
            'gripper': 0.0      # Tiempo acumulado pinza
        }
        # No necesitamos selección de articulaciones para calibración manual
        log.info("Manual Controller initialized")

    def run(self):
        """Main manual control loop"""
        print("\n" + "="*50)
        print("🤖 CONTROL MANUAL DEL BRAZO ROBÓTICO")
        print("="*50)
        print("CONTROL POR TIEMPO - MOVIMIENTOS SEGUROS")
        print("\nINSTRUCCIONES:")
        print("1. CONECTA la alimentación de los servos")
        print("2. Los movimientos están LIMITADOS por seguridad física")
        print("3. Usa comandos de tiempo para mover articulaciones")
        print("\nComandos de movimiento:")
        print("  b+<seg> - Base derecha (ej: b+1.5)")
        print("  b-<seg> - Base izquierda (ej: b-1.5)")
        print("  s+<seg> - Hombro arriba (ej: s+1.0)")
        print("  s-<seg> - Hombro abajo (ej: s-1.0)")
        print("  e+<seg> - Codo extender (ej: e+2.0)")
        print("  e-<seg> - Codo contraer (ej: e-2.0)")
        print("  g+<seg> - Pinza abrir (ej: g+1.0)")
        print("  g-<seg> - Pinza cerrar (ej: g-1.0)")
        print("\nComandos de estado:")
        print("  r       - Mostrar tiempos acumulados")
        print("  c       - Resetear tiempos acumulados")
        print("  home    - Ir a posición home")
        print("  test    - Ejecutar secuencia de prueba")
        print("  q       - Salir")
        print("\nEjemplo de uso:")
        print("  Mover base a la derecha 1 segundo → 'b+1'")
        print("  Subir hombro 0.5 segundos → 's+0.5'")
        print("  Presiona 'r' para ver tiempos acumulados")
        print("="*50)
        self.show_current_times()

        while True:
            try:
                cmd = input("\ncalibrar> ").strip().lower()

                if cmd == 'q':
                    break
                elif cmd == 'r':
                    self.show_current_times()
                elif cmd == 'c':
                    self.clear_times()
                elif cmd == 'home':
                    self.go_home()
                elif cmd == 'test':
                    self.test_sequence()
                elif cmd.startswith(('b', 's', 'e', 'g')):
                    self.parse_time_command(cmd)
                else:
                    print("❌ Usa: b<ángulo>, s<ángulo>, e<ángulo>, g<ángulo>, r (mostrar), c (limpiar), q (salir)")

            except KeyboardInterrupt:
                print("\n👋 Saliendo del control manual...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        self.show_current_times()
        self.cleanup()

    def parse_time_command(self, cmd):
        """Parse and execute time-based movement command"""
        try:
            if len(cmd) < 3 or cmd[1] not in ['+', '-']:
                print("❌ Formato inválido. Usa: b+1.5, s-0.5, e+2.0, g-1.0")
                return

            joint_letter = cmd[0]
            direction = 1 if cmd[1] == '+' else -1
            time_str = cmd[2:]

            try:
                tiempo_segundos = float(time_str)
            except ValueError:
                print("❌ Tiempo debe ser un número decimal. Ej: 1.5, 0.5, 2.0")
                return

            # Validar límites de tiempo (máximo 5 segundos por movimiento)
            if not (0.1 <= tiempo_segundos <= 5.0):
                print("❌ El tiempo debe estar entre 0.1-5.0 segundos")
                return

            # Mapear comandos a articulaciones
            joint_map = {
                'b': ('base', 'Base', self.controlador_robot.mover_base_tiempo),
                's': ('shoulder', 'Hombro', self.controlador_robot.mover_hombro_tiempo),
                'e': ('elbow', 'Codo', self.controlador_robot.mover_codo_tiempo),
                'g': ('gripper', 'Pinza', self.controlador_robot.mover_pinza_tiempo)
            }

            if joint_letter not in joint_map:
                print("❌ Articulación inválida. Usa: b (base), s (hombro), e (codo), g (pinza)")
                return

            joint, display_name, move_function = joint_map[joint_letter]

            # Ejecutar movimiento con límites físicos
            tiempo_real = move_function(direction, tiempo_segundos, velocidad=1.0)

            # Actualizar estado local
            self.current_times[joint] += tiempo_real * direction

            direction_name = {
                'b': ("DERECHA" if direction == 1 else "IZQUIERDA"),
                's': ("ARRIBA" if direction == 1 else "ABAJO"),
                'e': ("EXTENDER" if direction == 1 else "CONTRAER"),
                'g': ("ABRIR" if direction == 1 else "CERRAR")
            }[joint_letter]

            print(f"✅ MOVIMIENTO: {display_name} {direction_name} {tiempo_real:.1f}s")

        except Exception as e:
            print(f"❌ Error de movimiento: {e}")

    def adjust_angle(self, delta):
        """Adjust current joint by delta degrees"""
        if self.selected_joint == 'arm':
            # Para el brazo, ajustar arriba/abajo
            direction = 1 if delta > 0 else -1
            distance = abs(delta)
            # SOLO registrar movimiento - NO mover físicamente
            print(f"✅ REGISTRADO: Brazo {'ARRIBA' if direction > 0 else 'ABAJO'} {distance}mm")
        else:
            # Para servos - movimientos más pequeños y lentos
            current = self.current_angles[self.selected_joint]
            new_angle = current + delta

            # Validar límites - todos los servos configurados para 360°
            new_angle = max(0, min(360, new_angle))

            if new_angle != current:
                joint_names = {
                    'base': 'Base',
                    'shoulder': 'Hombro',
                    'elbow': 'Codo',
                    'gripper': 'Pinza'
                }

                display_name = joint_names[self.selected_joint]
                # SOLO registrar el ángulo - NO mover físicamente
                self.current_angles[self.selected_joint] = new_angle
                print(f"✅ REGISTRADO: {display_name} en {new_angle}°")
            else:
                print("📍 Límite alcanzado")

    def select_next_joint(self):
        """Select next joint"""
        current_index = self.joint_names.index(self.selected_joint)
        next_index = (current_index + 1) % len(self.joint_names)
        self.selected_joint = self.joint_names[next_index]
        print(f"🔄 Articulación seleccionada: {self.selected_joint}")

    def select_previous_joint(self):
        """Select previous joint"""
        current_index = self.joint_names.index(self.selected_joint)
        prev_index = (current_index - 1) % len(self.joint_names)
        self.selected_joint = self.joint_names[prev_index]
        print(f"🔄 Articulación seleccionada: {self.selected_joint}")

    def show_current_times(self):
        """Show current accumulated times of all joints"""
        print("\n⏱️ TIEMPOS ACUMULADOS (segundos):")
        print(f"  Base:     {self.current_times['base']:+.1f}s")
        print(f"  Hombro:   {self.current_times['shoulder']:+.1f}s")
        print(f"  Codo:     {self.current_times['elbow']:+.1f}s")
        print(f"  Pinza:    {self.current_times['gripper']:+.1f}s")
        print("\n💡 Valores positivos = movimiento en una dirección")
        print("💡 Valores negativos = movimiento en dirección opuesta")

    def clear_times(self):
        """Reset all accumulated times"""
        self.current_times = {
            'base': 0.0,
            'shoulder': 0.0,
            'elbow': 0.0,
            'gripper': 0.0
        }
        self.controlador_robot.resetear_tiempos()
        print("✅ Todos los tiempos reseteados")

    def go_home(self):
        """Move all joints to home position using time-based movements"""
        print("🏠 Yendo a posición home...")
        try:
            # Movimientos para regresar a posición home (aproximada)
            # Estos movimientos están limitados por seguridad física
            self.controlador_robot.mover_base_tiempo(-1, 1.5, velocidad=1.0)   # Ajuste base
            time.sleep(0.2)
            self.controlador_robot.mover_hombro_tiempo(-1, 1.0, velocidad=1.0) # Ajuste hombro
            time.sleep(0.2)
            self.controlador_robot.mover_codo_tiempo(1, 1.5, velocidad=1.0)    # Ajuste codo
            time.sleep(0.2)
            self.controlador_robot.mover_pinza_tiempo(1, 0.5, velocidad=1.0)   # Abrir pinza

            # Resetear contadores de tiempo
            self.clear_times()
            print("✅ Posición home alcanzada")
            self.show_current_times()
        except Exception as e:
            print(f"❌ Error yendo a home: {e}")

    def test_sequence(self):
        """Run a test sequence to verify all time-based movements"""
        print("🧪 Ejecutando secuencia de prueba con movimientos temporizados...")

        try:
            # Test base rotation
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
            time.sleep(0.3)

            # Test arm stepper
            print("Probando brazo stepper...")
            self.controlador_robot.mover_brazo(10, direccion=-1, velocidad=500)  # Abajo
            time.sleep(0.3)
            self.controlador_robot.mover_brazo(10, direccion=1, velocidad=500)   # Arriba
            time.sleep(0.3)

            print("✅ Secuencia de prueba completada!")
            self.show_current_times()

        except Exception as e:
            print(f"❌ Prueba fallida: {e}")

    def cleanup(self):
        """Clean shutdown"""
        print("🔌 Apagando...")
        try:
            self.controlador_robot.cerrar()
            print("✅ Control manual cerrado")
        except Exception as e:
            print(f"❌ Error durante apagado: {e}")


if __name__ == '__main__':
    controller = ManualController()
    controller.run()
