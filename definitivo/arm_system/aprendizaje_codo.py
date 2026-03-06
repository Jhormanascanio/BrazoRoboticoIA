#!/usr/bin/env python3
"""
APRENDIZAJE DEL CODO - Registra tus movimientos
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

CANAL_CODO = 1
PULSO_NEUTRAL = 1720  # Neutral real (sin carga)
PULSO_HOLD = 1850     # Compensa gravedad (ajusta si sigue bajando: 1900, 1950...)
PULSO_EXTENDER = 2200
PULSO_CONTRAER = 1200

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
    print("🧠 APRENDIZAJE DEL CODO")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✅ Listo | Canal {CANAL_CODO} | Neutral: {PULSO_NEUTRAL}µs\n")
    
    print("📋 INSTRUCCIONES:")
    print("  W - EXTENDER (mantén presionado)")
    print("  S - CONTRAER (mantén presionado)")
    print("  M - MARCAR límite extendido")
    print("  N - MARCAR límite contraído")
    print("  Q - GUARDAR y SALIR\n")
    input("Presiona ENTER...")
    
    aplicar_pulso(pca, CANAL_CODO, PULSO_NEUTRAL)
    
    tiempo_extender_total = 0.0
    tiempo_contraer_total = 0.0
    limite_extendido_marcado = False
    limite_contraido_marcado = False
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
                        if estado_actual != 'extender':
                            print("\r⬆️  EXTENDIENDO (M=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_CODO, PULSO_EXTENDER)
                            estado_actual = 'extender'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 's':
                        if estado_actual != 'contraer':
                            print("\r⬇️  CONTRAYENDO (N=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_CODO, PULSO_CONTRAER)
                            estado_actual = 'contraer'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 'm':
                        if estado_actual == 'extender':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_extender_total = tiempo_movimiento
                            limite_extendido_marcado = True
                            print(f"\n✅ EXTENDIDO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_CODO, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'n':
                        if estado_actual == 'contraer':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_contraer_total = tiempo_movimiento
                            limite_contraido_marcado = True
                            print(f"\n✅ CONTRAÍDO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_CODO, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'q':
                        print("\n\n💾 Guardando...")
                        aplicar_pulso(pca, CANAL_CODO, PULSO_NEUTRAL)
                        break
                else:
                    if estado_actual != 'detenido':
                        if estado_actual == 'extender' and tiempo_inicio_movimiento:
                            tiempo_extender_total += time.time() - tiempo_inicio_movimiento
                        elif estado_actual == 'contraer' and tiempo_inicio_movimiento:
                            tiempo_contraer_total += time.time() - tiempo_inicio_movimiento
                        print(f"\r⏹️  MANTENIENDO (compensa gravedad)        ", end='', flush=True)
                        aplicar_pulso(pca, CANAL_CODO, PULSO_HOLD)  # Usa PULSO_HOLD en lugar de NEUTRAL
                        estado_actual = 'detenido'
                        tiempo_inicio_movimiento = None
                
                time.sleep(0.02)
        
        datos = {
            "timestamp": datetime.now().isoformat(),
            "servo": "codo",
            "canal": CANAL_CODO,
            "pulso_neutral": PULSO_NEUTRAL,
            "pulso_extender": PULSO_EXTENDER,
            "pulso_contraer": PULSO_CONTRAER,
            "limites": {
                "extendido_marcado": limite_extendido_marcado,
                "contraido_marcado": limite_contraido_marcado,
                "tiempo_extender_max": round(tiempo_extender_total, 2),
                "tiempo_contraer_max": round(tiempo_contraer_total, 2)
            }
        }
        
        with open('aprendizaje_codo.json', 'w') as f:
            json.dump(datos, f, indent=2)
        
        print("\n" + "="*60)
        print(f"  • EXTENDER: {tiempo_extender_total:.2f}s")
        print(f"  • CONTRAER: {tiempo_contraer_total:.2f}s")
        print("💾 aprendizaje_codo.json")
        print("="*60)
    
    except KeyboardInterrupt:
        aplicar_pulso(pca, CANAL_CODO, PULSO_NEUTRAL)

if __name__ == '__main__':
    main()
