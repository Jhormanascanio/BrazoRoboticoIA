#!/usr/bin/env python3
"""
Test simple del hardware - verificar que motores funcionan
"""
import time
from control.robot_controller import ControladorRobotico

print("="*60)
print("TEST DE HARDWARE - BRAZO ROBÓTICO")
print("="*60)

print("\n1. Inicializando controlador...")
try:
    robot = ControladorRobotico()
    print("   ✓ Controlador inicializado correctamente")
except Exception as e:
    print(f"   ✗ ERROR al inicializar: {e}")
    exit(1)

print("\n2. Probando MOTOR PASO A PASO (giro horizontal)...")
print("   Girando derecha 20mm...")
try:
    robot.mover_brazo(20, direccion=1, velocidad=800)
    time.sleep(1)
    print("   ✓ Movimiento derecha completado")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("   Girando izquierda 20mm...")
try:
    robot.mover_brazo(20, direccion=-1, velocidad=800)
    time.sleep(1)
    print("   ✓ Movimiento izquierda completado")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n3. Probando SERVOS (movimiento vertical - hombro)...")
print("   Subiendo 0.5s...")
try:
    robot.mover_hombro_tiempo(1, 0.5, velocidad=0.5)
    time.sleep(0.2)
    robot.controlador_servo.detener_servo('hombro')  # DETENER EXPLÍCITO
    print("   ✓ Movimiento arriba completado y DETENIDO")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("   Bajando 0.5s...")
try:
    robot.mover_hombro_tiempo(-1, 0.5, velocidad=0.5)
    time.sleep(0.2)
    robot.controlador_servo.detener_servo('hombro')  # DETENER EXPLÍCITO
    print("   ✓ Movimiento abajo completado y DETENIDO")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n4. Probando CODO...")
try:
    robot.mover_codo_tiempo(1, 0.3, velocidad=0.5)
    time.sleep(0.2)
    robot.controlador_servo.detener_servo('codo')  # DETENER
    time.sleep(0.3)
    robot.mover_codo_tiempo(-1, 0.3, velocidad=0.5)
    time.sleep(0.2)
    robot.controlador_servo.detener_servo('codo')  # DETENER
    print("   ✓ Codo funciona y DETENIDO")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n5. Probando PINZA...")
try:
    robot.accion_recoger()  # Abrir
    time.sleep(1)
    robot.accion_soltar()  # Cerrar
    print("   ✓ Pinza funciona")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n6. Deteniendo motores...")
try:
    robot.controlador_servo.detener_todos()  # Detener TODOS los servos
    time.sleep(0.5)
    robot.cerrar()
    print("   ✓ Todos los motores detenidos y cerrado")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "="*60)
print("TEST COMPLETADO")
print("="*60)
print("\n¿Se movió el brazo físicamente? Si NO:")
print("  1. Verifica conexiones I2C en GPIO3/GPIO2")
print("  2. Verifica que PCA9685 tiene alimentación")
print("  3. Ejecuta: i2cdetect -y 1")
print("  4. Debes ver 0x40 en la salida")
