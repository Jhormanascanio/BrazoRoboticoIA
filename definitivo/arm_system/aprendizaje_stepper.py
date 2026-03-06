#!/usr/bin/env python3
"""
APRENDIZAJE DEL MOTOR PASO A PASO - Calibración de movimiento horizontal
"""
import time
from gpiozero import OutputDevice
import sys
import tty
import termios
import select
import json
from datetime import datetime

# CONFIGURACIÓN TMC2208
PIN_STEP = 14  # GPIO14 - Pulsos de paso
PIN_DIR = 15   # GPIO15 - Dirección
PIN_ENABLE = None  # Sin pin enable en tu configuración

# CONFIGURACIÓN MOTOR
PASOS_POR_REV = 200  # Motor NEMA 17 típico
MICROPASOS = 16      # TMC2208 en modo 1/16
PASOS_TOTALES = PASOS_POR_REV * MICROPASOS  # 3200 pasos/revolución

# VELOCIDAD (pasos por segundo)
VELOCIDAD_LENTA = 400    # Para movimientos precisos
VELOCIDAD_MEDIA = 800    # Para movimientos normales
VELOCIDAD_RAPIDA = 1200  # Para movimientos rápidos

class ControlTeclado:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
    
    def __enter__(self):
        tty.setraw(self.fd)
        return self
    
    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
    
    def get_key(self, timeout=0.05):
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.read(1)
        return None

class ControladorStepper:
    def __init__(self):
        self.pin_step = OutputDevice(PIN_STEP)
        self.pin_dir = OutputDevice(PIN_DIR)
        self.pin_enable = OutputDevice(PIN_ENABLE) if PIN_ENABLE else None
        self.pasos_acumulados = 0
        
        if self.pin_enable:
            self.pin_enable.off()  # Habilitar motor (activo bajo)
    
    def mover_pasos(self, pasos, direccion, velocidad):
        """Mover cantidad específica de pasos
        
        Args:
            pasos: Número de pasos a mover
            direccion: 1 = derecha, -1 = izquierda
            velocidad: Pasos por segundo
        """
        self.pin_dir.value = 1 if direccion > 0 else 0
        delay = 1.0 / velocidad / 2  # Mitad del período
        
        for _ in range(abs(pasos)):
            self.pin_step.on()
            time.sleep(delay)
            self.pin_step.off()
            time.sleep(delay)
        
        self.pasos_acumulados += pasos * direccion
    
    def obtener_posicion_mm(self, paso_tornillo_mm=8):
        """Calcular posición en mm (asumiendo tornillo trapezoidal de 8mm/rev)"""
        revoluciones = self.pasos_acumulados / PASOS_TOTALES
        return revoluciones * paso_tornillo_mm
    
    def resetear_posicion(self):
        """Resetear contador de posición"""
        self.pasos_acumulados = 0

def main():
    print("="*60)
    print("🔧 APRENDIZAJE DEL MOTOR PASO A PASO")
    print("="*60)
    print(f"GPIO: STEP={PIN_STEP}, DIR={PIN_DIR}")
    print(f"Configuración: {PASOS_POR_REV} pasos/rev × {MICROPASOS} micropasos = {PASOS_TOTALES}")
    print()
    
    stepper = ControladorStepper()
    print("✅ Motor paso a paso inicializado\n")
    
    print("📋 INSTRUCCIONES:")
    print("  A - Mover IZQUIERDA (100 pasos)")
    print("  D - Mover DERECHA (100 pasos)")
    print("  1 - Velocidad LENTA (400 pasos/s)")
    print("  2 - Velocidad MEDIA (800 pasos/s)")
    print("  3 - Velocidad RÁPIDA (1200 pasos/s)")
    print("  R - RESETEAR posición a 0")
    print("  M - MARCAR límites (izquierda/derecha)")
    print("  Q - GUARDAR y SALIR\n")
    
    input("Presiona ENTER para comenzar...")
    
    velocidad_actual = VELOCIDAD_MEDIA
    limite_izquierda = None
    limite_derecha = None
    pasos_por_movimiento = 100
    
    print(f"\n🟢 CONTROL ACTIVO | Velocidad: {velocidad_actual} pasos/s\n")
    
    try:
        with ControlTeclado() as control:
            while True:
                tecla = control.get_key()
                
                if tecla:
                    tecla = tecla.lower()
                    
                    if tecla == 'a':
                        print(f"← IZQUIERDA {pasos_por_movimiento} pasos... ", end='', flush=True)
                        stepper.mover_pasos(pasos_por_movimiento, -1, velocidad_actual)
                        pos_mm = stepper.obtener_posicion_mm()
                        print(f"✓ Pos: {stepper.pasos_acumulados} pasos ({pos_mm:.1f}mm)")
                    
                    elif tecla == 'd':
                        print(f"→ DERECHA {pasos_por_movimiento} pasos... ", end='', flush=True)
                        stepper.mover_pasos(pasos_por_movimiento, 1, velocidad_actual)
                        pos_mm = stepper.obtener_posicion_mm()
                        print(f"✓ Pos: {stepper.pasos_acumulados} pasos ({pos_mm:.1f}mm)")
                    
                    elif tecla == '1':
                        velocidad_actual = VELOCIDAD_LENTA
                        print(f"🐢 Velocidad LENTA: {velocidad_actual} pasos/s")
                    
                    elif tecla == '2':
                        velocidad_actual = VELOCIDAD_MEDIA
                        print(f"🚶 Velocidad MEDIA: {velocidad_actual} pasos/s")
                    
                    elif tecla == '3':
                        velocidad_actual = VELOCIDAD_RAPIDA
                        print(f"🏃 Velocidad RÁPIDA: {velocidad_actual} pasos/s")
                    
                    elif tecla == 'r':
                        stepper.resetear_posicion()
                        print("🔄 Posición reseteada a 0")
                    
                    elif tecla == 'm':
                        opcion = input("\n¿Marcar límite? (i=Izquierda, d=Derecha, c=Cancelar): ").lower()
                        if opcion == 'i':
                            limite_izquierda = stepper.pasos_acumulados
                            print(f"✅ Límite IZQUIERDA marcado: {limite_izquierda} pasos ({stepper.obtener_posicion_mm():.1f}mm)")
                        elif opcion == 'd':
                            limite_derecha = stepper.pasos_acumulados
                            print(f"✅ Límite DERECHA marcado: {limite_derecha} pasos ({stepper.obtener_posicion_mm():.1f}mm)")
                    
                    elif tecla == 'q':
                        print("\n\n💾 Guardando...")
                        break
                
                time.sleep(0.02)
        
        # Calcular rango total
        if limite_izquierda is not None and limite_derecha is not None:
            rango_pasos = abs(limite_derecha - limite_izquierda)
            rango_mm = rango_pasos / PASOS_TOTALES * 8  # Asumiendo tornillo 8mm/rev
        else:
            rango_pasos = 0
            rango_mm = 0
        
        datos = {
            "timestamp": datetime.now().isoformat(),
            "motor": "stepper_horizontal",
            "pines": {
                "step": PIN_STEP,
                "dir": PIN_DIR,
                "enable": PIN_ENABLE
            },
            "configuracion": {
                "pasos_por_revolucion": PASOS_POR_REV,
                "micropasos": MICROPASOS,
                "pasos_totales": PASOS_TOTALES,
                "paso_tornillo_mm": 8
            },
            "limites": {
                "limite_izquierda_pasos": limite_izquierda,
                "limite_derecha_pasos": limite_derecha,
                "rango_pasos": rango_pasos,
                "rango_mm": round(rango_mm, 2)
            },
            "velocidades_probadas": {
                "lenta": VELOCIDAD_LENTA,
                "media": VELOCIDAD_MEDIA,
                "rapida": VELOCIDAD_RAPIDA
            }
        }
        
        with open('aprendizaje_stepper.json', 'w') as f:
            json.dump(datos, f, indent=2)
        
        print("\n" + "="*60)
        print(f"  • Límite IZQUIERDA: {limite_izquierda} pasos")
        print(f"  • Límite DERECHA: {limite_derecha} pasos")
        print(f"  • Rango total: {rango_pasos} pasos ({rango_mm:.2f}mm)")
        print("💾 aprendizaje_stepper.json")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido")
    finally:
        if stepper.pin_enable:
            stepper.pin_enable.on()  # Deshabilitar motor

if __name__ == '__main__':
    main()
