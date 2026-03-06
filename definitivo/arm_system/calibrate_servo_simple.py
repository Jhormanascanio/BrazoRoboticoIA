#!/usr/bin/env python3
"""
Calibración de servos - SOLO SERVOS (sin motor paso a paso)
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685

print("="*60)
print("🔧 CALIBRACIÓN DE SERVOS - Modo Simple")
print("="*60)
print("\nEste script SOLO inicializa los servos (PCA9685)")
print("No usa el motor paso a paso.\n")

servo_name = input("¿Qué servo calibrar? (hombro/codo/muñeca/pinza): ").strip().lower()

if servo_name not in ['hombro', 'codo', 'muñeca', 'muneca', 'pinza']:
    print("Servo inválido")
    exit(1)

# Mapeo de servos a canales
servo_map = {
    'hombro': 0,
    'codo': 1,
    'muñeca': 2,
    'muneca': 2,
    'pinza': 3
}
canal = servo_map[servo_name]

print(f"\n✓ Inicializando PCA9685...")
try:
    # Inicializar I2C y PCA9685
    i2c = busio.I2C(board.D3, board.D2)  # GPIO3 (SCL), GPIO2 (SDA)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✓ PCA9685 inicializado en 0x40")
except Exception as e:
    print(f"✗ ERROR al inicializar PCA9685: {e}")
    exit(1)

print(f"\n✓ Calibrando servo: {servo_name} (Canal {canal})")
print("\n" + "="*60)
print("INSTRUCCIONES:")
print("="*60)
print("1. Localiza el TRIMMER en la parte trasera del servo")
print("2. Es un tornillo pequeño (Phillips o plano)")
print("3. Usa un destornillador pequeño")
print("4. Gira LENTAMENTE el trimmer:")
print("   - Horario ⟳ si el servo gira en un sentido")
print("   - Antihorario ⟲ si gira en el otro sentido")
print("5. El objetivo es que el servo NO SE MUEVA")
print("6. Puede requerir varios intentos")
print("\n⚠️  Presiona Ctrl+C cuando el servo esté DETENIDO")
print("="*60 + "\n")

input("Presiona ENTER para comenzar...")

print("\n🔄 Enviando pulso neutral 1500µs...")
print("   Ajusta el trimmer AHORA hasta que el servo se detenga\n")

try:
    # Calcular duty cycle para 1500µs (pulso neutral)
    # Fórmula: duty_cycle = (pulso_us / 20000) * 0xFFFF
    duty = int(1500 / 20000 * 0xFFFF)
    
    while True:
        pca.channels[canal].duty_cycle = duty
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\n✓ Calibración detenida por usuario")
    
    # Enviar pulso neutral una última vez
    pca.channels[canal].duty_cycle = duty
    time.sleep(0.5)
    
    # Desinicializar PCA9685
    pca.deinit()
    
    print("\n" + "="*60)
    print("CALIBRACIÓN COMPLETADA")
    print("="*60)
    print("\n¿El servo se detuvo completamente?")
    respuesta = input("(s/n): ").strip().lower()
    
    if respuesta == 's':
        print("\n✅ ¡PERFECTO! El servo está calibrado.")
        print("   Ahora puedes usar el sistema normalmente.")
        print("\n   Próximos pasos:")
        print("   1. Calibra los otros servos:")
        servos_faltantes = []
        for s in ['hombro', 'codo', 'muñeca', 'pinza']:
            if s != servo_name and s != 'muneca':
                servos_faltantes.append(s)
        print(f"      - {', '.join(servos_faltantes)}")
        print("   2. Ejecuta: python test_detection_web.py")
    else:
        print("\n⚠️  El servo todavía se mueve:")
        print("   - Ejecuta este script de nuevo")
        print("   - Ajusta el trimmer más fino")
        print("   - Puede necesitar varias iteraciones")
        print("\n   Video tutorial: https://youtu.be/vQx8V3d6jM8")

print("\n¡Hasta luego!")
