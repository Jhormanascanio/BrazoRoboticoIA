#!/usr/bin/env python3
"""
Diagnóstico PCA9685 - Verificar estado y resetear completamente
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685

def diagnosticar_pca9685():
    print("\n" + "="*60)
    print("🔍 DIAGNÓSTICO PCA9685")
    print("="*60)
    
    try:
        # Inicializar I2C
        print("\n1️⃣ Inicializando I2C...")
        i2c = busio.I2C(board.SCL, board.SDA)
        print("   ✅ I2C inicializado")
        
        # Escanear dispositivos I2C
        print("\n2️⃣ Escaneando bus I2C...")
        while not i2c.try_lock():
            pass
        
        devices = i2c.scan()
        i2c.unlock()
        
        print(f"   Dispositivos encontrados: {[hex(d) for d in devices]}")
        
        if 0x40 not in devices:
            print("   ❌ PCA9685 NO encontrado en 0x40")
            print("   🔧 Verifica conexiones:")
            print("      - SDA → GPIO2 (Pin 3)")
            print("      - SCL → GPIO3 (Pin 5)")
            print("      - VCC → 3.3V o 5V")
            print("      - GND → GND")
            return
        
        print("   ✅ PCA9685 encontrado en 0x40")
        
        # Conectar al PCA9685
        print("\n3️⃣ Conectando al PCA9685...")
        pca = PCA9685(i2c, address=0x40)
        pca.frequency = 50
        print("   ✅ Conectado, frecuencia: 50Hz")
        
        # Leer estado de canales
        print("\n4️⃣ Leyendo estado de canales...")
        for canal in range(4):
            try:
                # Intentar leer el duty_cycle del canal
                channel = pca.channels[canal]
                print(f"   Canal {canal}: OK")
            except Exception as e:
                print(f"   Canal {canal}: ERROR - {e}")
        
        # APAGAR TODOS LOS CANALES
        print("\n5️⃣ APAGANDO TODOS LOS CANALES...")
        for canal in range(16):
            pca.channels[canal].duty_cycle = 0
            print(f"   Canal {canal}: OFF", end="\r")
            time.sleep(0.05)
        
        print("\n   ✅ Todos los canales apagados")
        
        # Desinicializar PCA9685
        print("\n6️⃣ Desconectando PCA9685...")
        pca.deinit()
        print("   ✅ PCA9685 desconectado")
        
        print("\n" + "="*60)
        print("✅ DIAGNÓSTICO COMPLETADO")
        print("="*60)
        print("\n💡 Si el brazo SIGUE moviéndose:")
        print("   1. Hay un problema de HARDWARE")
        print("   2. Los servos pueden estar recibiendo señal de OTRO lugar")
        print("   3. Puede haber un cortocircuito")
        print("   4. DESCONECTA la alimentación 5V INMEDIATAMENTE")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🆘 ACCIÓN INMEDIATA:")
        print("   ⚠️  DESCONECTA LA ALIMENTACIÓN 5V DE LOS SERVOS")
    
    finally:
        try:
            pca.deinit()
        except:
            pass

if __name__ == '__main__':
    diagnosticar_pca9685()
