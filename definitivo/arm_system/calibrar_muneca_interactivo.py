#!/usr/bin/env python3
"""
CALIBRACIÓN INTERACTIVA MUÑECA
Ajusta el pulso en tiempo real hasta encontrar el que la detiene
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import tty
import termios
import select

CANAL_MUNECA = 2

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
    print("🎯 CALIBRACIÓN INTERACTIVA MUÑECA")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print("✅ PCA9685 inicializado\n")
    
    # Empezar con 1700 (el pulso que dijiste que funcionaba en calibrar_muneca_auto.py)
    pulso_actual = 1700
    
    print("📋 CONTROLES:")
    print("  + = Aumentar 10µs")
    print("  - = Disminuir 10µs")
    print("  ] = Aumentar 1µs")
    print("  [ = Disminuir 1µs")
    print("  ESPACIO = Aplicar pulso actual")
    print("  Q = SALIR")
    print()
    print("🎯 OBJETIVO: Encuentra el pulso donde NO SUBE NI BAJA")
    print()
    input("Presiona ENTER para empezar...")
    
    aplicar_pulso(pca, CANAL_MUNECA, pulso_actual)
    print(f"\n🔧 Pulso aplicado: {pulso_actual}µs")
    print("   Observa si sube, baja o se queda quieto...")
    
    try:
        with ControlTeclado() as control:
            while True:
                tecla = control.get_key()
                
                if tecla:
                    cambio = False
                    
                    if tecla == '+' or tecla == '=':
                        pulso_actual += 10
                        cambio = True
                    elif tecla == '-' or tecla == '_':
                        pulso_actual -= 10
                        cambio = True
                    elif tecla == ']':
                        pulso_actual += 1
                        cambio = True
                    elif tecla == '[':
                        pulso_actual -= 1
                        cambio = True
                    elif tecla == ' ':
                        cambio = True
                    elif tecla == 'q':
                        break
                    
                    if cambio:
                        aplicar_pulso(pca, CANAL_MUNECA, pulso_actual)
                        print(f"\r🔧 Pulso: {pulso_actual}µs (¿Sube/Baja/Quieto?)    ", end='', flush=True)
                
                time.sleep(0.02)
        
        print(f"\n\n🎯 PULSO ENCONTRADO: {pulso_actual}µs")
        print(f"\n📝 Actualiza aprendizaje_muneca.py:")
        print(f"   PULSO_NEUTRAL = {pulso_actual}")
        print(f"   PULSO_HOLD = {pulso_actual}")
        print()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido")
        print(f"Último pulso probado: {pulso_actual}µs")

if __name__ == '__main__':
    main()
