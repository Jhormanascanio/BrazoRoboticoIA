#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO TMC2208 - Verificación de hardware
"""
import time
from gpiozero import OutputDevice, InputDevice
import subprocess

print("="*60)
print("🔍 DIAGNÓSTICO TMC2208")
print("="*60)

# Configuración
PIN_STEP = 14
PIN_DIR = 15
PIN_ENABLE = 18  # Probar con GPIO18 si existe

print("\n1️⃣ VERIFICAR PINES GPIO")
print("-"*60)
try:
    pin_step = OutputDevice(PIN_STEP)
    pin_dir = OutputDevice(PIN_DIR)
    print(f"✅ GPIO{PIN_STEP} (STEP) - OK")
    print(f"✅ GPIO{PIN_DIR} (DIR) - OK")
    
    # Probar pin ENABLE
    try:
        pin_enable = OutputDevice(PIN_ENABLE)
        print(f"✅ GPIO{PIN_ENABLE} (ENABLE) disponible")
        
        # Intentar habilitar motor (EN es activo BAJO en TMC2208)
        print("\n🔧 Probando ENABLE...")
        print("   ENABLE = LOW (motor habilitado)")
        pin_enable.off()  # LOW = motor habilitado
        time.sleep(0.5)
        
    except:
        print(f"⚠️  GPIO{PIN_ENABLE} no disponible (ignorar si no usas ENABLE)")
        pin_enable = None
        
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n2️⃣ TEST DE MOVIMIENTO CON ENABLE HABILITADO")
print("-"*60)
if pin_enable:
    pin_enable.off()  # Asegurar que está habilitado
    
print("Generando 1000 pulsos (5 revoluciones)...")
velocidad = 200  # Muy lento para observar
delay = 1.0 / velocidad / 2

pin_dir.value = 1
for i in range(1000):
    if i % 100 == 0:
        print(f"  Pulsos: {i}/1000", end='\r')
    pin_step.on()
    time.sleep(delay)
    pin_step.off()
    time.sleep(delay)
print("\n✅ 1000 pulsos completados")

print("\n3️⃣ CHECKLIST DE HARDWARE")
print("-"*60)
print("Verifica estas conexiones en el TMC2208:")
print()
print("ALIMENTACIÓN:")
print("  [ ] VM (motor) conectado a 12V")
print("  [ ] VDD (lógica) conectado a 3.3V o 5V") 
print("  [ ] GND común entre Pi y TMC2208")
print()
print("SEÑALES DE CONTROL:")
print("  [ ] STEP conectado a GPIO14 (pin físico 8)")
print("  [ ] DIR conectado a GPIO15 (pin físico 10)")
print("  [ ] EN conectado a GND o GPIO18 (deshabilitar = HIGH, habilitar = LOW)")
print()
print("MOTOR:")
print("  [ ] Bobina A: cables al mismo color en A1/A2")
print("  [ ] Bobina B: cables al mismo color en B1/B2")
print("  [ ] Verificar que las bobinas NO estén cruzadas")
print()
print("CONFIGURACIÓN TMC2208:")
print("  [ ] Modo standalone (SIN UART) - pins MS1/MS2 determinan microstepping")
print("  [ ] VREF ajustado (~0.6V para NEMA17 1.5A)")
print("  [ ] Disipador de calor instalado en chip")
print()
print("4️⃣ PRUEBAS ADICIONALES")
print("-"*60)
print("1. Con multímetro:")
print("   • VM debe tener 12V")
print("   • VDD debe tener 3.3V o 5V")
print("   • STEP debe cambiar entre 0V y 3.3V al generar pulsos")
print()
print("2. LED indicador:")
print("   • Algunos TMC2208 tienen LED que parpadea con pulsos STEP")
print()
print("3. Sentir el motor:")
print("   • ¿Está caliente? (puede estar en cortocircuito)")
print("   • ¿Hace ruido/vibra? (está recibiendo señal pero no suficiente corriente)")
print()
print("4. VREF crítico:")
print("   • Mide voltaje entre potenciómetro y GND")
print("   • Debe ser 0.5-0.8V para NEMA17")
print("   • Si es 0V o muy bajo, el motor no tendrá fuerza")
print()
print("="*60)
print("💡 PROBLEMA MÁS COMÚN: VREF mal ajustado o EN no habilitado")
print("="*60)

# Limpiar
if pin_enable:
    pin_enable.on()  # Deshabilitar motor al terminar
