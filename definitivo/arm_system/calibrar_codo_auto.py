#!/usr/bin/env python3
"""
CALIBRACIÓN AUTOMÁTICA CODO - Prueba rango amplio
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685

CANAL_CODO = 1

def aplicar_pulso(pca, canal, pulso_us):
    duty_cycle = int(pulso_us / 20000 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle
    print(f"  Aplicado: {pulso_us}µs", flush=True)

def main():
    print("="*60)
    print("🔍 CALIBRACIÓN AUTOMÁTICA CODO")
    print("="*60)
    
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print("✅ Listo\n")
    
    # Rango AMPLIO: 1400-1900µs en pasos de 20µs
    pulsos = list(range(1400, 1900, 20))
    
    print("📋 INSTRUCCIONES:")
    print("  - Voy a probar pulsos de 1400µs a 1900µs")
    print("  - Cada pulso se mantiene 3 segundos")
    print("  - OBSERVA cuál detiene el codo COMPLETAMENTE")
    print("  - ANOTA el valor donde se detiene\n")
    
    input("Presiona ENTER para comenzar...")
    
    for pulso in pulsos:
        print(f"\n{'='*60}")
        print(f"🔍 PROBANDO: {pulso}µs")
        print(f"{'='*60}")
        
        aplicar_pulso(pca, CANAL_CODO, pulso)
        
        print("⏱️  Observa 3 segundos...", end=" ", flush=True)
        time.sleep(3)
        print("✓")
        
        respuesta = input("\n¿Se DETUVO? (s=SÍ y SALIR / n=NO continuar / q=SALIR): ").lower()
        
        if respuesta == 's':
            print(f"\n🎯 ¡PULSO NEUTRAL ENCONTRADO: {pulso}µs!")
            print(f"\n📝 ANOTA ESTE VALOR: {pulso}µs")
            print("\n✅ Ahora actualiza aprendizaje_codo.py línea 17:")
            print(f"   PULSO_NEUTRAL = {pulso}")
            aplicar_pulso(pca, CANAL_CODO, pulso)
            time.sleep(2)
            break
        elif respuesta == 'q':
            print("\n👋 Calibración cancelada")
            break
    else:
        print("\n⚠️  NO se encontró pulso neutral en rango 1400-1900µs")
        print("\n💡 POSIBLES CAUSAS:")
        print("  1. Servo defectuoso - considera reemplazarlo")
        print("  2. Peso del brazo - la gravedad siempre lo mueve")
        print("  3. Conexión floja - verifica cable al PCA9685")
        print("  4. Alimentación insuficiente - verifica 5V/20A")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción detectada")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
