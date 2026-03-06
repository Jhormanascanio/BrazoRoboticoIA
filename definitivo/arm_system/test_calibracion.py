#!/usr/bin/env python3
"""
Test rápido para verificar que los servos se detienen con pulsos calibrados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from control.robot_controller import ControladorRobotico
import time

print("="*60)
print("🧪 TEST DE PULSOS CALIBRADOS")
print("="*60)

# Inicializar robot (sin motor paso a paso)
try:
    robot = ControladorRobotico(habilitar_stepper=False)
    print("✅ Robot inicializado correctamente")
    print(f"   Pulsos neutrales cargados:")
    for nombre, servo in robot.controlador_servo.servos.items():
        print(f"     {nombre}: {servo['pulso_neutral']}µs")
except Exception as e:
    print(f"❌ Error inicializando robot: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("PRUEBA 1: Mover y detener HOMBRO")
print("="*60)

input("\nPresiona ENTER para mover hombro...")

print("\n➡️  Moviendo hombro ARRIBA por 1 segundo...")
robot.mover_hombro_tiempo('arriba', 1.0, velocidad=0.3)
time.sleep(0.5)

print("⏹️  ¿El servo se DETUVO completamente?")
respuesta1 = input("(s/n): ").strip().lower()

print("\n⬅️  Moviendo hombro ABAJO por 1 segundo...")
robot.mover_hombro_tiempo('abajo', 1.0, velocidad=0.3)
time.sleep(0.5)

print("⏹️  ¿El servo se DETUVO completamente?")
respuesta2 = input("(s/n): ").strip().lower()

print("\n" + "="*60)
print("PRUEBA 2: Mover y detener CODO")
print("="*60)

input("\nPresiona ENTER para mover codo...")

print("\n➡️  Moviendo codo ARRIBA por 1 segundo...")
robot.mover_codo_tiempo('arriba', 1.0, velocidad=0.3)
time.sleep(0.5)

print("⏹️  ¿El servo se DETUVO completamente?")
respuesta3 = input("(s/n): ").strip().lower()

print("\n⬅️  Moviendo codo ABAJO por 1 segundo...")
robot.mover_codo_tiempo('abajo', 1.0, velocidad=0.3)
time.sleep(0.5)

print("⏹️  ¿El servo se DETUVO completamente?")
respuesta4 = input("(s/n): ").strip().lower()

# Detener todos
robot.detener_todos_servos()

print("\n" + "="*60)
print("RESULTADO DEL TEST")
print("="*60)

resultados = [respuesta1, respuesta2, respuesta3, respuesta4]
exitosos = resultados.count('s')

print(f"\nServos que se detuvieron: {exitosos}/4")

if exitosos == 4:
    print("\n✅ ¡PERFECTO! Todos los servos se detienen correctamente")
    print("\n🎯 PRÓXIMO PASO:")
    print("   Ejecuta el sistema de detección completo:")
    print("   python test_detection_web.py")
    print("\n   Abre en el navegador: http://IP_DE_TU_PI:5000")
    print("   El brazo debería seguir objetos y DETENERSE correctamente")
    
elif exitosos >= 2:
    print("\n⚠️  Algunos servos se detienen, otros no")
    print("   - Si son hombro/codo los que funcionan: puedes usar el sistema")
    print("   - Si muñeca/pinza no se detienen: calibra de nuevo esos servos")
    print(f"\n   Ejecuta: python calibrar_forzado.py")
    print("   Y recalibra solo los servos problemáticos")
    
else:
    print("\n❌ La mayoría de servos NO se detienen")
    print("   Posibles causas:")
    print("   1. servo_config.json no se cargó correctamente")
    print("   2. Los pulsos calibrados no son correctos")
    print("   3. Problema de alimentación")
    print("\n   Verifica:")
    print("   - Que existe servo_config.json en el directorio")
    print("   - Ejecuta: cat servo_config.json")
    print("   - Alimentación del PCA9685 (5-6V, 2-3A mínimo)")

print("\n¡Test completado!")
