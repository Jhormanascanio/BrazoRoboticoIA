#!/usr/bin/env python3
"""
CALIBRACIÓN AUTOMÁTICA MUÑECA - Encuentra pulso neutral
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685

CANAL_MUNECA = 2

def aplicar_pulso(pca, canal, pulso_us):
    duty_cycle = int(pulso_us / 20000 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle
    print(f"  Aplicado: {pulso_us}µs", flush=True)

def main():
    print("="*60)
    print("🔍 CALIBRACIÓN AUTOMÁTICA MUÑECA")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print("✅ Listo\n")
    
    # Rango amplio
    pulsos = list(range(1500, 1900, 20))
    
    print("📋 Buscaré pulso neutral de 1500µs a 1900µs")
    print("   OBSERVA cuál detiene la muñeca completamente\n")
    
    input("Presiona ENTER...")
    
    for pulso in pulsos:
        print(f"\n{'='*60}")
        print(f"🔍 PROBANDO: {pulso}µs")
        print(f"{'='*60}")
        
        aplicar_pulso(pca, CANAL_MUNECA, pulso)
        
        print("⏱️  Observa 3 segundos...", end=" ", flush=True)
        time.sleep(3)
        print("✓")
        
        respuesta = input("\n¿Se DETUVO? (s=SÍ/n=NO/q=SALIR): ").lower()
        
        if respuesta == 's':
            print(f"\n🎯 ¡PULSO NEUTRAL ENCONTRADO: {pulso}µs!")
            print(f"\n📝 Actualiza aprendizaje_muneca.py línea 17:")
            print(f"   PULSO_NEUTRAL = {pulso}")
            aplicar_pulso(pca, CANAL_MUNECA, pulso)
            time.sleep(2)
            break
        elif respuesta == 'q':
            break
    else:
        print("\n⚠️  No encontrado en 1500-1900µs")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
