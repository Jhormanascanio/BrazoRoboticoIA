#!/usr/bin/env python3
"""
APRENDIZAJE DE LA PINZA - Registra tus movimientos
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

CANAL_PINZA = 3
PULSO_NEUTRAL = 1690  # Valor calibrado - detiene perfectamente
PULSO_ABRIR = 2300    # Abre completamente en ~0.61s
PULSO_CERRAR = 1100   # Cierra completamente en ~0.61s

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
    print("🧠 APRENDIZAJE DE LA PINZA")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✅ Listo | Canal {CANAL_PINZA} | Neutral: {PULSO_NEUTRAL}µs\n")
    
    print("📋 INSTRUCCIONES:")
    print("  W - ABRIR")
    print("  S - CERRAR")
    print("  M - MARCAR límite abierto")
    print("  N - MARCAR límite cerrado")
    print("  Q - GUARDAR y SALIR\n")
    input("Presiona ENTER...")
    
    aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)
    
    tiempo_abrir_total = 0.0
    tiempo_cerrar_total = 0.0
    limite_abierto_marcado = False
    limite_cerrado_marcado = False
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
                        if estado_actual != 'abrir':
                            print("\r🤏 ABRIENDO (M=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_PINZA, PULSO_ABRIR)
                            estado_actual = 'abrir'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 's':
                        if estado_actual != 'cerrar':
                            print("\r✊ CERRANDO (N=marcar)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_PINZA, PULSO_CERRAR)
                            estado_actual = 'cerrar'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 'm':
                        if estado_actual == 'abrir':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_abrir_total = tiempo_movimiento
                            limite_abierto_marcado = True
                            print(f"\n✅ ABIERTO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'n':
                        if estado_actual == 'cerrar':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_cerrar_total = tiempo_movimiento
                            limite_cerrado_marcado = True
                            print(f"\n✅ CERRADO: {tiempo_movimiento:.2f}s")
                            aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                    
                    elif tecla == 'q':
                        print("\n\n💾 Guardando...")
                        aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)
                        break
                else:
                    if estado_actual != 'detenido':
                        if estado_actual == 'abrir' and tiempo_inicio_movimiento:
                            tiempo_abrir_total += time.time() - tiempo_inicio_movimiento
                        elif estado_actual == 'cerrar' and tiempo_inicio_movimiento:
                            tiempo_cerrar_total += time.time() - tiempo_inicio_movimiento
                        print(f"\r⏹️  DETENIDO        ", end='', flush=True)
                        aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)
                        estado_actual = 'detenido'
                        tiempo_inicio_movimiento = None
                
                time.sleep(0.02)
        
        datos = {
            "timestamp": datetime.now().isoformat(),
            "servo": "pinza",
            "canal": CANAL_PINZA,
            "pulso_neutral": PULSO_NEUTRAL,
            "pulso_abrir": PULSO_ABRIR,
            "pulso_cerrar": PULSO_CERRAR,
            "limites": {
                "abierto_marcado": limite_abierto_marcado,
                "cerrado_marcado": limite_cerrado_marcado,
                "tiempo_abrir_max": round(tiempo_abrir_total, 2),
                "tiempo_cerrar_max": round(tiempo_cerrar_total, 2)
            }
        }
        
        with open('aprendizaje_pinza.json', 'w') as f:
            json.dump(datos, f, indent=2)
        
        print("\n" + "="*60)
        print(f"  • ABRIR: {tiempo_abrir_total:.2f}s")
        print(f"  • CERRAR: {tiempo_cerrar_total:.2f}s")
        print("💾 aprendizaje_pinza.json")
        print("="*60)
    
    except KeyboardInterrupt:
        aplicar_pulso(pca, CANAL_PINZA, PULSO_NEUTRAL)

if __name__ == '__main__':
    main()
