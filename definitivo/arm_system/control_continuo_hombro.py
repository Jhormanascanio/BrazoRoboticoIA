#!/usr/bin/env python3
"""
CONTROL CONTINUO HOMBRO - Tipo joystick
Mantén presionada la tecla para mover, suelta para detener
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import tty
import termios
import select

CANAL_HOMBRO = 0
PULSO_NEUTRAL = 1700
PULSO_SUBIR = 1200
PULSO_BAJAR = 2200

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
        """Lee tecla sin bloquear"""
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.read(1)
        return None

def aplicar_pulso(pca, canal, pulso_us):
    """Aplicar pulso específico"""
    duty_cycle = int(pulso_us / 20000 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle

def main():
    print("="*60)
    print("🎮 CONTROL CONTINUO HOMBRO")
    print("="*60)
    
    # Inicializar PCA9685
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✅ Listo | Neutral: {PULSO_NEUTRAL}µs\n")
    
    print("📋 CONTROLES (mantén presionado):")
    print("  W - SUBIR")
    print("  S - BAJAR")
    print("  (suelta para DETENER)")
    print("  Q - SALIR\n")
    print("Presiona cualquier tecla para comenzar...")
    input()
    
    # Detener al inicio
    aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
    
    print("\n🟢 CONTROL ACTIVO - Mantén W/S presionado\n")
    
    estado_actual = 'detenido'
    
    try:
        with ControlTeclado() as control:
            while True:
                tecla = control.get_key()
                
                if tecla:
                    tecla = tecla.lower()
                    
                    if tecla == 'w':
                        if estado_actual != 'subir':
                            print("\r⬆️  SUBIENDO...    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_SUBIR)
                            estado_actual = 'subir'
                    
                    elif tecla == 's':
                        if estado_actual != 'bajar':
                            print("\r⬇️  BAJANDO...     ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_BAJAR)
                            estado_actual = 'bajar'
                    
                    elif tecla == 'q':
                        print("\n\n👋 Saliendo...")
                        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                        break
                
                else:
                    # No hay tecla presionada - DETENER
                    if estado_actual != 'detenido':
                        print(f"\r⏹️  DETENIDO        ", end='', flush=True)
                        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                        estado_actual = 'detenido'
                
                time.sleep(0.02)  # 50Hz actualización
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción")
        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)

if __name__ == '__main__':
    main()
