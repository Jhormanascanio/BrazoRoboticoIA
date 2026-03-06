#!/usr/bin/env python3
"""
CONTROL MANUAL CONTINUO - Mantén presionada la tecla para movimiento continuo
"""
import sys
import time
sys.path.append('/home/harol/Documents/Articulado/brazo/definitivo')

from arm_system.control.robot_controller import ControladorRobotico
import tty
import termios
import select

class ControlTeclado:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
    
    def __enter__(self):
        tty.setraw(self.fd)
        return self
    
    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
    
    def get_key(self, timeout=0.05):
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.read(1)
        return None

print("="*60)
print("🎮 CONTROL MANUAL DEL BRAZO")
print("="*60)
print("\nCONTROLES:")
print()
print("  HOMBRO:")
print("    3 - Subir")
print("    4 - Bajar")
print()
print("  CODO:")
print("    5 - Extender")
print("    6 - Contraer")
print()
print("  MUÑECA:")
print("    7 - Rotar horario")
print("    8 - Rotar antihorario")
print()
print("  PINZA:")
print("    A - Abrir")
print("    S - Cerrar")
print()
print("  D - DETENER TODO")
print("  Q - SALIR")
print()
print("="*60)

robot = ControladorRobotico(habilitar_stepper=False)
print("✅ Robot listo\n")

# Obtener referencias a servos y extraer valores necesarios
servos = robot.controlador_servo.servos

# Extraer configuración de cada servo con valores por defecto
hombro_neutral = servos['shoulder'].get('pulso_neutral', 1700)
hombro_hold = servos['shoulder'].get('pulso_hold', 1700)
codo_neutral = servos['elbow'].get('pulso_neutral', 1720)
codo_hold = servos['elbow'].get('pulso_hold', 1850)
muneca_neutral = servos['wrist'].get('pulso_neutral', 1682)
muneca_hold = servos['wrist'].get('pulso_hold', 1800)
pinza_neutral = servos['gripper'].get('pulso_neutral', 1690)
pinza_hold = servos['gripper'].get('pulso_hold', 1690)

# Canales
canal_hombro = servos['shoulder']['canal']
canal_codo = servos['elbow']['canal']
canal_muneca = servos['wrist']['canal']
canal_pinza = servos['gripper']['canal']

# Obtener objeto PCA9685
pca = robot.controlador_servo.pca

# Pulsos de movimiento
PULSO_RAPIDO = 500  # Offset para movimiento rápido

print(f"📊 Configuración cargada:")
print(f"  Hombro: neutral={hombro_neutral}, hold={hombro_hold}")
print(f"  Codo: neutral={codo_neutral}, hold={codo_hold}")
print(f"  Muñeca: neutral={muneca_neutral}, hold={muneca_hold}")
print(f"  Pinza: neutral={pinza_neutral}, hold={pinza_hold}")

input("\nPresiona ENTER para comenzar...")

# Estados de teclas presionadas
teclas_activas = set()

print("\n🟢 CONTROL ACTIVO - Mantén presionada la tecla para movimiento continuo\n")

def aplicar_pulso_directo(canal, pulso_us):
    """Aplica un pulso directamente al canal PCA9685"""
    duty_cycle = int(pulso_us / 20000.0 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle

try:
    with ControlTeclado() as control:
        while True:
            tecla = control.get_key()
            
            # Actualizar set de teclas activas
            if tecla:
                tecla_lower = tecla.lower()
                
                # SALIR
                if tecla_lower == 'q':
                    break
                
                # DETENER TODO
                elif tecla_lower == 'd':
                    teclas_activas.clear()
                    robot.controlador_servo.detener_todos()
                    print("\r⏹️  DETENIDO          ", end='', flush=True)
                    continue
                
                # Agregar tecla a activas
                teclas_activas.add(tecla_lower)
            
            # Aplicar movimientos según teclas activas
            movimiento_activo = False
            
            # HOMBRO
            if '3' in teclas_activas:
                print("\r⬆️  HOMBRO ARRIBA    ", end='', flush=True)
                aplicar_pulso_directo(canal_hombro, hombro_neutral + PULSO_RAPIDO)
                movimiento_activo = True
            elif '4' in teclas_activas:
                print("\r⬇️  HOMBRO ABAJO     ", end='', flush=True)
                aplicar_pulso_directo(canal_hombro, hombro_neutral - PULSO_RAPIDO)
                movimiento_activo = True
            
            # CODO
            elif '5' in teclas_activas:
                print("\r↗️  CODO EXTENDER    ", end='', flush=True)
                aplicar_pulso_directo(canal_codo, codo_neutral + PULSO_RAPIDO)
                movimiento_activo = True
            elif '6' in teclas_activas:
                print("\r↘️  CODO CONTRAER    ", end='', flush=True)
                aplicar_pulso_directo(canal_codo, codo_neutral - PULSO_RAPIDO)
                movimiento_activo = True
            
            # MUÑECA
            elif '7' in teclas_activas:
                print("\r🔄 MUÑECA HORARIO   ", end='', flush=True)
                aplicar_pulso_directo(canal_muneca, muneca_neutral - PULSO_RAPIDO)
                movimiento_activo = True
            elif '8' in teclas_activas:
                print("\r🔃 MUÑECA ANTIHORARIO", end='', flush=True)
                aplicar_pulso_directo(canal_muneca, muneca_neutral + PULSO_RAPIDO)
                movimiento_activo = True
            
            # PINZA
            elif 'a' in teclas_activas:
                print("\r🤏 PINZA ABRIR      ", end='', flush=True)
                aplicar_pulso_directo(canal_pinza, 2300)
                movimiento_activo = True
            elif 's' in teclas_activas:
                print("\r✊ PINZA CERRAR     ", end='', flush=True)
                aplicar_pulso_directo(canal_pinza, 1100)
                movimiento_activo = True
            
            # Si no hay tecla activa, aplicar hold
            if not movimiento_activo:
                if len(teclas_activas) == 0:
                    aplicar_pulso_directo(canal_hombro, hombro_hold)
                    aplicar_pulso_directo(canal_codo, codo_hold)
                    aplicar_pulso_directo(canal_muneca, muneca_hold)
                    aplicar_pulso_directo(canal_pinza, pinza_hold)
                    print("\r⏸️  En hold          ", end='', flush=True)
                
                # Limpiar teclas no válidas
                teclas_activas = {t for t in teclas_activas if t in '345678asdq'}
            
            time.sleep(0.05)
    
    # Detener todo al salir
    robot.controlador_servo.detener_todos()
    print("\n\n⏹️  Sistema detenido")
    print("="*60)

except KeyboardInterrupt:
    robot.controlador_servo.detener_todos()
    print("\n\n⚠️  Interrumpido - Servos detenidos")
except Exception as e:
    robot.controlador_servo.detener_todos()
    print(f"\n\n❌ Error: {e}")
    print("Servos detenidos por seguridad")
