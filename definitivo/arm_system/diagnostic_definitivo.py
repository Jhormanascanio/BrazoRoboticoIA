#!/usr/bin/env python3
"""
Test de diagnóstico DEFINITIVO para identificar tipo de servo
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685

print("="*60)
print("🔍 DIAGNÓSTICO DEFINITIVO - TIPO DE SERVO")
print("="*60)

# Inicializar PCA9685
print("\nInicializando PCA9685...")
i2c = busio.I2C(board.D3, board.D2)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

SERVOS = {
    'hombro': 0,
    'codo': 1,
    'muñeca': 2,
    'pinza': 3
}

def pulso_a_duty_cycle(pulso_us):
    """Convertir microsegundos a duty cycle"""
    periodo_ms = 1000.0 / 50
    duty = int((pulso_us / 1000.0) / periodo_ms * 65535)
    return duty

def aplicar_pulso(canal, pulso_us):
    """Aplicar pulso a canal"""
    duty = pulso_a_duty_cycle(pulso_us)
    pca.channels[canal].duty_cycle = duty

# Seleccionar servo
print("\nSelecciona un servo para diagnosticar:")
for i, nombre in enumerate(SERVOS.keys(), 1):
    print(f"  {i}. {nombre.upper()}")

while True:
    try:
        opcion = int(input("\nElige (1-4): "))
        if 1 <= opcion <= 4:
            servo_nombre = list(SERVOS.keys())[opcion-1]
            servo_canal = SERVOS[servo_nombre]
            break
    except ValueError:
        pass

print(f"\n📌 Diagnosticando: {servo_nombre.upper()}")
print("="*60)

# TEST 1: Pulso 1000µs
print("\n--- TEST 1: Pulso 1000µs (5 segundos) ---")
print("OBSERVA el servo:")
aplicar_pulso(servo_canal, 1000)
time.sleep(5)

print("\nPregunta 1: ¿Qué hizo el servo?")
print("  A) Se movió a una posición y SE DETUVO")
print("  B) GIRÓ CONTINUAMENTE en una dirección")
print("  C) No hizo nada")
resp1 = input("Respuesta (A/B/C): ").strip().upper()

# TEST 2: Pulso 1500µs
print("\n--- TEST 2: Pulso 1500µs (5 segundos) ---")
aplicar_pulso(servo_canal, 1500)
time.sleep(5)

print("\nPregunta 2: ¿Qué hizo el servo?")
print("  A) Se movió a una posición y SE DETUVO")
print("  B) GIRÓ CONTINUAMENTE (puede ser lento)")
print("  C) Se quedó quieto (detenido)")
resp2 = input("Respuesta (A/B/C): ").strip().upper()

# TEST 3: Pulso 2000µs
print("\n--- TEST 3: Pulso 2000µs (5 segundos) ---")
aplicar_pulso(servo_canal, 2000)
time.sleep(5)

print("\nPregunta 3: ¿Qué hizo el servo?")
print("  A) Se movió a una posición y SE DETUVO")
print("  B) GIRÓ CONTINUAMENTE en dirección opuesta a Test 1")
print("  C) No hizo nada")
resp3 = input("Respuesta (A/B/C): ").strip().upper()

# Detener
aplicar_pulso(servo_canal, 1500)

# ANÁLISIS
print("\n" + "="*60)
print("RESULTADO DEL DIAGNÓSTICO")
print("="*60)

if resp1 == 'A' and resp2 == 'A' and resp3 == 'A':
    print("\n✅ Tu servo es POSICIONAL (0-180°)")
    print("\n📝 Características:")
    print("  - Se mueve a una posición específica y SE DETIENE")
    print("  - Pulsos diferentes = posiciones diferentes")
    print("  - NO tiene trimmer")
    print("\n🔧 SOLUCIÓN:")
    print("  Debes usar control por ÁNGULO con adafruit_motor.servo")
    print("  Tu código actual (control por tiempo) NO funciona con esto.")
    print("\n  Necesito REFACTORIZAR robot_controller.py completamente.")
    
elif resp1 == 'B' and resp2 == 'C' and resp3 == 'B':
    print("\n✅ Tu servo es CONTINUO (360°) y está CALIBRADO")
    print("\n📝 Características:")
    print("  - 1000µs = gira en una dirección")
    print("  - 1500µs = se DETIENE")
    print("  - 2000µs = gira en dirección opuesta")
    print("\n🔧 SOLUCIÓN:")
    print("  Tu código actual está bien diseñado.")
    print("  Solo necesitas actualizar PULSO_NEUTRAL = 1500 en robot_controller.py")
    
elif resp1 == 'B' and resp2 == 'B' and resp3 == 'B':
    print("\n⚠️  Tu servo es CONTINUO (360°) pero NO CALIBRADO")
    print("\n📝 Problema:")
    print("  El servo gira continuamente con todos los pulsos")
    print("  Esto significa que NO tiene trimmer O está descalibrado de fábrica")
    print("\n🔧 SOLUCIONES:")
    print("  A) Buscar con lupa/microscopio si tiene trimmer oculto")
    print("  B) Reemplazar por servos continuos con trimmer")
    print("  C) Usar servos posicionales y refactorizar código")
    
else:
    print("\n❓ Comportamiento mixto o poco claro")
    print(f"\nRespuestas: Test1={resp1}, Test2={resp2}, Test3={resp3}")
    print("\nPosibles causas:")
    print("  - Servo defectuoso")
    print("  - Alimentación insuficiente")
    print("  - Servo modificado/hackeado incorrectamente")

# Preguntar información adicional
print("\n" + "="*60)
print("INFORMACIÓN ADICIONAL")
print("="*60)
print("\n¿Dónde compraste estos servos?")
print("¿Qué modelo EXACTO dice en la etiqueta del servo?")
vendedor = input("Respuesta: ").strip()

print("\n¿El servo tiene algún tornillo pequeño visible en los lados?")
tiene_tornillo = input("(s/n): ").strip().lower()

print("\n📝 Guardando información...")
with open('servo_diagnostic.txt', 'w') as f:
    f.write(f"Servo: {servo_nombre}\n")
    f.write(f"Test 1 (1000µs): {resp1}\n")
    f.write(f"Test 2 (1500µs): {resp2}\n")
    f.write(f"Test 3 (2000µs): {resp3}\n")
    f.write(f"Vendedor/Modelo: {vendedor}\n")
    f.write(f"Tiene tornillo visible: {tiene_tornillo}\n")

print("✓ Información guardada en servo_diagnostic.txt")

# Limpiar
time.sleep(0.5)
pca.deinit()
print("\n¡Diagnóstico completado!")
