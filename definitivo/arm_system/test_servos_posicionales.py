#!/usr/bin/env python3
"""
Test de servos POSICIONALES MG996R (0-180 grados)
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

print("="*60)
print("🔧 TEST DE SERVOS POSICIONALES MG996R")
print("="*60)
print("\nLos MG996R son servos posicionales (0-180°)")
print("Se controlan por ÁNGULO, no por tiempo.\n")

# Inicializar PCA9685
print("Inicializando PCA9685...")
i2c = busio.I2C(board.D3, board.D2)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

# Crear objetos servo para cada canal
servos = {
    'hombro': servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500),
    'codo': servo.Servo(pca.channels[1], min_pulse=500, max_pulse=2500),
    'muñeca': servo.Servo(pca.channels[2], min_pulse=500, max_pulse=2500),
    'pinza': servo.Servo(pca.channels[3], min_pulse=500, max_pulse=2500)
}

print("✓ PCA9685 inicializado")
print("\n" + "="*60)
print("PRUEBA DE MOVIMIENTO")
print("="*60)
print("\nVamos a mover cada servo a diferentes ángulos:")
print("  0° (izquierda)")
print("  90° (centro)")  
print("  180° (derecha)")
print("\nObserva si los servos se mueven Y SE DETIENEN en cada posición.\n")

input("Presiona ENTER para comenzar...")

for nombre, servo_obj in servos.items():
    print(f"\n--- Probando {nombre.upper()} (Canal {list(servos.keys()).index(nombre)}) ---")
    
    # Mover a 90° (centro)
    print(f"  Moviendo a 90° (centro)...")
    servo_obj.angle = 90
    time.sleep(1.5)
    
    # Mover a 0°
    print(f"  Moviendo a 0° (izquierda)...")
    servo_obj.angle = 0
    time.sleep(1.5)
    
    # Mover a 180°
    print(f"  Moviendo a 180° (derecha)...")
    servo_obj.angle = 180
    time.sleep(1.5)
    
    # Volver a 90°
    print(f"  Volviendo a 90° (centro)...")
    servo_obj.angle = 90
    time.sleep(1.5)
    
    print(f"  ✓ {nombre} completado")

print("\n" + "="*60)
print("PRUEBA COMPLETADA")
print("="*60)
print("\n¿Los servos se movieron correctamente y se DETUVIERON?")
respuesta = input("(s/n): ").strip().lower()

if respuesta == 's':
    print("\n✅ ¡PERFECTO! Los servos funcionan correctamente.")
    print("\nAhora el problema es que tu código usa control por TIEMPO")
    print("pero los MG996R necesitan control por ÁNGULO.")
    print("\nTienes 2 opciones:")
    print("  A) Modificar robot_controller.py para usar ángulos")
    print("  B) Conseguir servos continuos de verdad (360°)")
else:
    print("\n⚠️  Los servos NO funcionan correctamente:")
    print("  1. Verifica alimentación del PCA9685 (5-6V)")
    print("  2. Verifica conexiones I2C (GPIO2/GPIO3)")
    print("  3. Ejecuta: i2cdetect -y 1 (debe mostrar 0x40)")

# Limpiar
pca.deinit()
print("\n¡Listo!")
