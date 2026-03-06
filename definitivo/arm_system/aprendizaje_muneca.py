#!/usr/bin/env python3
"""
APRENDIZAJE DE LA MUÑECA - Registra tus movimientos
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import tty
import termios
import select
import json
from datetime import datetime

CANAL_MUNECA = 2
PULSO_NEUTRAL = 1682  # Valor calibrado - detiene perfectamente
PULSO_HOLD = 1690     # Pulso de mantenimiento con compensación mínima
PULSO_HORARIO = 1400  # INVERTIDO: W baja correctamente
PULSO_ANTIHORARIO = 2000  # INVERTIDO: S sube correctamente

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

def aplicar_pulso(pca, canal, pulso_us):
    duty_cycle = int(pulso_us / 20000 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle

def main():
    print("="*60)
    print("🧠 APRENDIZAJE DE LA MUÑECA")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✅ Listo | Canal {CANAL_MUNECA} | Neutral: {PULSO_NEUTRAL}µs\n")
    
    print("📋 INSTRUCCIONES:")
    print("  W - ROTAR HORARIO")
    print("  S - ROTAR ANTIHORARIO")
    print("  M - MARCAR límite horario")
    print("  N - MARCAR límite antihorario")
    print("  Q - GUARDAR y SALIR\n")
    input("Presiona ENTER...")
    
    aplicar_pulso(pca, CANAL_MUNECA, PULSO_NEUTRAL)
    
    tiempo_horario_total = 0.0
    tiempo_antihorario_total = 0.0
    limite_horario_marcado = False
    limite_antihorario_marcado = False
    estado_actual = 'detenido'
    tiempo_inicio_movimiento = None
    
    print("\n🟢 CONTROL ACTIVO\n")
    
    try:
        with ControlTeclado() as control:
            while True:
                tecla = control.get_key()
                
                if tecla:
                    tecla = tecla.lower()
                    
                    if tecla == 'w':
                        if estado_actual != 'horario':
                            print("\r🔄 HORARIO (M=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_MUNECA, PULSO_HORARIO)
                            estado_actual = 'horario'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 's':
                        if estado_actual != 'antihorario':
                            print("\r🔄 ANTIHORARIO (N=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_MUNECA, PULSO_ANTIHORARIO)
                            estado_actual = 'antihorario'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 'm':
                        if estado_actual == 'horario':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_horario_total = tiempo_movimiento
                            limite_horario_marcado = True
                            print(f"\n✅ HORARIO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_MUNECA, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'n':
                        if estado_actual == 'antihorario':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_antihorario_total = tiempo_movimiento
                            limite_antihorario_marcado = True
                            print(f"\n✅ ANTIHORARIO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_MUNECA, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'q':
                        print("\n\n💾 Guardando...")
                        aplicar_pulso(pca, CANAL_MUNECA, PULSO_NEUTRAL)
                        break
                else:
                    if estado_actual != 'detenido':
                        if estado_actual == 'horario' and tiempo_inicio_movimiento:
                            tiempo_horario_total += time.time() - tiempo_inicio_movimiento
                        elif estado_actual == 'antihorario' and tiempo_inicio_movimiento:
                            tiempo_antihorario_total += time.time() - tiempo_inicio_movimiento
                        print(f"\r⏹️  DETENIDO        ", end='', flush=True)
                        aplicar_pulso(pca, CANAL_MUNECA, PULSO_HOLD)  # Usar PULSO_HOLD en vez de NEUTRAL
                        estado_actual = 'detenido'
                        tiempo_inicio_movimiento = None
                
                time.sleep(0.02)
        
        datos = {
            "timestamp": datetime.now().isoformat(),
            "servo": "muneca",
            "canal": CANAL_MUNECA,
            "pulso_neutral": PULSO_NEUTRAL,
            "pulso_horario": PULSO_HORARIO,
            "pulso_antihorario": PULSO_ANTIHORARIO,
            "limites": {
                "horario_marcado": limite_horario_marcado,
                "antihorario_marcado": limite_antihorario_marcado,
                "tiempo_horario_max": round(tiempo_horario_total, 2),
                "tiempo_antihorario_max": round(tiempo_antihorario_total, 2)
            }
        }
        
        with open('aprendizaje_muneca.json', 'w') as f:
            json.dump(datos, f, indent=2)
        
        print("\n" + "="*60)
        print(f"  • HORARIO: {tiempo_horario_total:.2f}s")
        print(f"  • ANTIHORARIO: {tiempo_antihorario_total:.2f}s")
        print("💾 aprendizaje_muneca.json")
        print("="*60)
    
    except KeyboardInterrupt:
        aplicar_pulso(pca, CANAL_MUNECA, PULSO_NEUTRAL)

if __name__ == '__main__':
    main()
