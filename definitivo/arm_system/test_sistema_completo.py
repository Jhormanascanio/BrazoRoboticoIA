#!/usr/bin/env python3
"""
TEST COMPLETO DEL SISTEMA - Verificar todos los servos con compensación de gravedad
"""
import sys
import time
sys.path.append('/home/harol/Documents/Articulado/brazo/definitivo')

from arm_system.control.robot_controller import ControladorRobotico
import logging

logging.basicConfig(level=logging.INFO)

print("="*60)
print("🤖 TEST COMPLETO DEL SISTEMA")
print("="*60)
print("Este test verificará:")
print("  1. Todos los servos se detienen correctamente")
print("  2. Compensación de gravedad funciona (codo y muñeca)")
print("  3. Movimientos suaves y controlados")
print()

# Inicializar robot SIN stepper (TMC2208 dañado)
robot = ControladorRobotico(habilitar_stepper=False)

print("✅ Robot inicializado")
print("   - Hombro (shoulder) canal 0")
print("   - Codo (elbow) canal 1")
print("   - Muñeca (wrist) canal 2")
print("   - Pinza (gripper) canal 3")
print()

input("Presiona ENTER para comenzar las pruebas...")

# TEST 1: HOMBRO
print("\n" + "="*60)
print("TEST 1: HOMBRO (shoulder)")
print("="*60)
print("Moviendo hombro ARRIBA 1 segundo...")
robot.mover_hombro_tiempo(direccion=1, tiempo_segundos=1.0, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo correctamente? (debe estar quieto)")

print("\nMoviendo hombro ABAJO 1 segundo...")
robot.mover_hombro_tiempo(direccion=-1, tiempo_segundos=1.0, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo correctamente?")

# TEST 2: CODO (con compensación de gravedad)
print("\n" + "="*60)
print("TEST 2: CODO (elbow) - CON COMPENSACIÓN DE GRAVEDAD")
print("="*60)
print("Moviendo codo EXTENDER 1 segundo...")
robot.mover_codo_tiempo(direccion=1, tiempo_segundos=1.0, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo y se mantiene en posición? (sin caer)")

print("\nMoviendo codo CONTRAER 0.5 segundos...")
robot.mover_codo_tiempo(direccion=-1, tiempo_segundos=0.5, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo y se mantiene en posición?")

# TEST 3: MUÑECA (con compensación de gravedad)
print("\n" + "="*60)
print("TEST 3: MUÑECA (wrist) - CON COMPENSACIÓN DE GRAVEDAD")
print("="*60)
print("Rotando muñeca 1 segundo...")
robot.controlador_servo.mover_por_tiempo('wrist', direccion=1, tiempo_segundos=1.0, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo sin oscilar?")

print("\nRotando muñeca dirección opuesta 1 segundo...")
robot.controlador_servo.mover_por_tiempo('wrist', direccion=-1, tiempo_segundos=1.0, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo sin oscilar?")

# TEST 4: PINZA
print("\n" + "="*60)
print("TEST 4: PINZA (gripper)")
print("="*60)
print("Abriendo pinza 0.6 segundos...")
robot.mover_pinza_tiempo(direccion=1, tiempo_segundos=0.6, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo correctamente?")

print("\nCerrando pinza 0.6 segundos...")
robot.mover_pinza_tiempo(direccion=-1, tiempo_segundos=0.6, velocidad=0.5)
time.sleep(2)
print("✓ ¿Se detuvo correctamente?")

# Detener todos los servos
print("\n" + "="*60)
print("DETENIENDO TODOS LOS SERVOS")
print("="*60)
robot.controlador_servo.detener_todos()
print("✅ Todos los servos detenidos con pulso_hold")

print("\n" + "="*60)
print("✅ TEST COMPLETO FINALIZADO")
print("="*60)
print("\nRESULTADOS:")
print("  [ ] Hombro se detiene correctamente")
print("  [ ] Codo se mantiene en posición (no cae)")
print("  [ ] Muñeca se detiene sin oscilar")
print("  [ ] Pinza se detiene correctamente")
print()
print("Si todos funcionan correctamente:")
print("  ✅ Sistema calibrado y listo para usar")
print()
print("Si alguno falla:")
print("  ⚠️  Revisar valores en servo_config.json")
print("  ⚠️  Ajustar pulso_hold si hay gravedad")
print("="*60)
