#!/usr/bin/env python3
"""
TEST SIMPLE MOTOR PASO A PASO - Diagnóstico básico
"""
import time
from gpiozero import OutputDevice

# Configuración
PIN_STEP = 14
PIN_DIR = 15

print("="*60)
print("🔍 TEST SIMPLE MOTOR PASO A PASO")
print("="*60)
print(f"PIN_STEP (pulsos): GPIO{PIN_STEP}")
print(f"PIN_DIR (dirección): GPIO{PIN_DIR}")
print()

# Inicializar pines
try:
    pin_step = OutputDevice(PIN_STEP)
    pin_dir = OutputDevice(PIN_DIR)
    print("✅ Pines inicializados correctamente\n")
except Exception as e:
    print(f"❌ Error inicializando pines: {e}")
    exit(1)

# Test 1: Verificar que los pines responden
print("TEST 1: Verificar pines GPIO")
print("  Encendiendo DIR...")
pin_dir.on()
time.sleep(0.5)
print("  Apagando DIR...")
pin_dir.off()
time.sleep(0.5)
print("  ✓ PIN_DIR funciona\n")

# Test 2: Generar pulsos lentos visibles
print("TEST 2: Generar 10 pulsos LENTOS (debería ver parpadeo LED si está conectado)")
pin_dir.value = 1  # Dirección 1
for i in range(10):
    print(f"  Pulso {i+1}/10", end='\r')
    pin_step.on()
    time.sleep(0.1)  # 100ms encendido
    pin_step.off()
    time.sleep(0.1)  # 100ms apagado
print("  ✓ 10 pulsos generados\n")

# Test 3: Pulsos más rápidos (movimiento real)
print("TEST 3: Generar 200 pulsos RÁPIDOS (1 revolución si micropasos=1)")
print("  ¿El motor se mueve? Observa...")
velocidad = 400  # pasos por segundo
delay = 1.0 / velocidad / 2

pin_dir.value = 1
for i in range(200):
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)
print("  ✓ 200 pulsos completados\n")

# Test 4: Cambiar dirección
print("TEST 4: Cambiar dirección y 200 pulsos más")
pin_dir.value = 0  # Dirección opuesta
for i in range(200):
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)
print("  ✓ 200 pulsos en dirección opuesta\n")

print("="*60)
print("DIAGNÓSTICO:")
print("  1. ¿Viste parpadear algún LED en el TMC2208? (STEP)")
print("  2. ¿El motor hizo algún sonido (zumbido)?")
print("  3. ¿El motor se movió aunque sea mínimamente?")
print()
print("Si NO se movió:")
print("  • Verifica alimentación 12V al TMC2208 (VM)")
print("  • Verifica conexiones motor (A1, A2, B1, B2)")
print("  • Verifica que TMC2208 esté en modo UART o standalone correcto")
print("  • Prueba invertir cables del motor")
print("  • Mide voltaje VREF del driver (debe ser ~0.6V para NEMA17)")
print("="*60)
