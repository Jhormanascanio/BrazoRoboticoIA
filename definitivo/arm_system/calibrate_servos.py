#!/usr/bin/env python3
"""
Calibración de servos continuos MG996R
Encuentra el pulso EXACTO que detiene cada servo
"""
from control.robot_controller import ControladorRobotico
import time

print("="*60)
print("🔧 CALIBRACIÓN DE SERVOS CONTINUOS MG996R")
print("="*60)
print("\nLos servos continuos tienen un trimmer (potenciómetro pequeño)")
print("en la parte trasera que ajusta el punto muerto.")
print("\nSi el servo se mueve con pulso 1500µs, hay 2 soluciones:")
print("  A) Ajustar el trimmer físicamente (recomendado)")
print("  B) Encontrar el pulso correcto por software")
print("\n" + "="*60)

servo_name = input("\n¿Qué servo calibrar? (hombro/codo/muñeca/pinza): ").strip().lower()

if servo_name not in ['hombro', 'codo', 'muñeca', 'muneca', 'pinza']:
    print("Servo inválido")
    exit(1)

print(f"\nCalibrando servo: {servo_name}")
print("\nVamos a probar diferentes pulsos entre 1400-1600µs")
print("Observa cuál detiene completamente el servo.\n")

robot = ControladorRobotico()

# Obtener canal del servo
servo_map = {
    'hombro': 0,
    'codo': 1,
    'muñeca': 2,
    'muneca': 2,  # Aceptar sin tilde también
    'pinza': 3
}
canal = servo_map[servo_name]

print("Probando pulsos...\n")

# Probar diferentes pulsos
for pulso in range(1400, 1601, 10):  # De 1400 a 1600 en pasos de 10
    duty = int(pulso / 20000 * 0xFFFF)
    robot.controlador_servo.pca.channels[canal].duty_cycle = duty
    
    print(f"Pulso: {pulso}µs - ¿Se detuvo? Esperando 2s...")
    time.sleep(2)
    
    respuesta = input("¿Este pulso DETIENE el servo? (s/n/q para salir): ").strip().lower()
    
    if respuesta == 's':
        print(f"\n✓ ¡ENCONTRADO! Pulso correcto: {pulso}µs")
        print(f"\nPara usar este valor, modifica robot_controller.py:")
        print(f"  Cambiar línea 'pulso = 1500' a 'pulso = {pulso}'")
        break
    elif respuesta == 'q':
        print("Calibración cancelada")
        break

# Detener
duty = int(1500 / 20000 * 0xFFFF)
robot.controlador_servo.pca.channels[canal].duty_cycle = duty

robot.cerrar()

print("\n" + "="*60)
print("CALIBRACIÓN COMPLETADA")
print("="*60)
print("\nSi NO encontraste un pulso que detenga el servo:")
print("  1. Ajusta el trimmer físicamente en la parte trasera")
print("  2. Gira el trimmer con destornillador pequeño")
print("  3. Prueba hasta que el servo NO se mueva con señal neutral")
print("\nReferencia: https://youtu.be/vQx8V3d6jM8")
