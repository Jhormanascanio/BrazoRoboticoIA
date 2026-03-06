#!/usr/bin/env python3
"""
TEST POST-AJUSTE VREF - Verificar movimiento motor
"""
import time
from gpiozero import OutputDevice

PIN_STEP = 14
PIN_DIR = 15
PIN_ENABLE = 18

print("="*60)
print("🔧 TEST POST-AJUSTE VREF")
print("="*60)
print("⚠️  ANTES DE EJECUTAR:")
print("   1. Ajusta VREF a 0.6V con multímetro")
print("   2. Verifica 12V en VM del TMC2208")
print("   3. Asegura que motor esté bien conectado")
print()
input("Presiona ENTER cuando esté listo...")

# Inicializar
pin_step = OutputDevice(PIN_STEP)
pin_dir = OutputDevice(PIN_DIR)
pin_enable = OutputDevice(PIN_ENABLE)

# Habilitar motor (EN = LOW)
pin_enable.off()
print("\n✅ Motor habilitado (EN=LOW)")
time.sleep(0.5)

# Test LENTO - deberías poder ver girar el eje
print("\n🐢 TEST 1: Movimiento LENTO (200 pasos)")
print("   Observa el eje del motor...")
pin_dir.value = 1
delay = 0.005  # 5ms = muy lento

for i in range(200):
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)
    if i % 50 == 0:
        print(f"   Paso {i}/200", end='\r')

print("\n   ✓ Completado")
time.sleep(1)

# Test dirección opuesta
print("\n🔄 TEST 2: Dirección opuesta")
pin_dir.value = 0
for i in range(200):
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)

print("   ✓ Completado")

# Test velocidad media
print("\n🏃 TEST 3: Velocidad MEDIA (1000 pasos)")
pin_dir.value = 1
delay = 0.00125  # 400 pasos/s

for i in range(1000):
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)

print("   ✓ Completado")

# Deshabilitar motor
pin_enable.on()
print("\n⏹️  Motor deshabilitado")

print("\n" + "="*60)
print("RESULTADO:")
print("  ¿Se movió el motor? (S/N): ", end='')
respuesta = input().lower()

if respuesta == 's':
    print("\n✅ ¡ÉXITO! El motor funciona correctamente")
    print("   Ahora puedes usar aprendizaje_stepper.py")
else:
    print("\n❌ El motor NO se movió")
    print("\nVERIFICA:")
    print("  1. VREF = 0.6V (crítico)")
    print("  2. VM = 12V en TMC2208")
    print("  3. Cables del motor bien conectados")
    print("  4. Motor no está trabado mecánicamente")
    print("  5. Disipador de calor en TMC2208")
    print("\n💡 Si todo está correcto, el TMC2208 puede estar dañado")

print("="*60)
