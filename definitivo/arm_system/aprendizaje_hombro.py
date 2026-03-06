#!/usr/bin/env python3
"""
APRENDIZAJE DEL HOMBRO - Registra tus movimientos
El sistema aprenderá los límites y comportamiento observándote
"""
import time
import board
import busio
from adafruit_pca9685 import PCA9685
import sys
import tty
import termios
import select
import json
from datetime import datetime

CANAL_HOMBRO = 0
PULSO_NEUTRAL = 1700
PULSO_SUBIR = 1200
PULSO_BAJAR = 2200

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
        """Lee tecla sin bloquear"""
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.read(1)
        return None

def aplicar_pulso(pca, canal, pulso_us):
    """Aplicar pulso específico"""
    duty_cycle = int(pulso_us / 20000 * 0xFFFF)
    pca.channels[canal].duty_cycle = duty_cycle

def main():
    print("="*60)
    print("🧠 APRENDIZAJE DEL HOMBRO")
    print("="*60)
    
    # Inicializar PCA9685
    i2c = busio.I2C(board.D3, board.D2)
    pca = PCA9685(i2c, address=0x40)
    pca.frequency = 50
    print(f"✅ Listo | Neutral: {PULSO_NEUTRAL}µs\n")
    
    print("📋 INSTRUCCIONES:")
    print("  W - SUBIR (mantén presionado)")
    print("  S - BAJAR (mantén presionado)")
    print("  M - MARCAR límite superior (cuando llegue arriba)")
    print("  N - MARCAR límite inferior (cuando llegue abajo)")
    print("  Q - GUARDAR datos y SALIR\n")
    print("💡 Mueve el brazo y marca los límites cuando veas que")
    print("   está en su posición máxima/mínima segura\n")
    input("Presiona ENTER para comenzar...")
    
    # Detener al inicio
    aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
    
    # Variables de aprendizaje
    tiempo_inicio = time.time()
    tiempo_subir_total = 0.0
    tiempo_bajar_total = 0.0
    limite_superior_marcado = False
    limite_inferior_marcado = False
    
    print("\n🟢 CONTROL ACTIVO - Empieza a mover el hombro\n")
    
    estado_actual = 'detenido'
    tiempo_inicio_movimiento = None
    
    try:
        with ControlTeclado() as control:
            while True:
                tecla = control.get_key()
                
                if tecla:
                    tecla = tecla.lower()
                    
                    if tecla == 'w':
                        if estado_actual != 'subir':
                            print("\r⬆️  SUBIENDO... (presiona M cuando llegue arriba)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_SUBIR)
                            estado_actual = 'subir'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 's':
                        if estado_actual != 'bajar':
                            print("\r⬇️  BAJANDO... (presiona N cuando llegue abajo)    ", end='', flush=True)
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_BAJAR)
                            estado_actual = 'bajar'
                            tiempo_inicio_movimiento = time.time()
                    
                    elif tecla == 'm':
                        if estado_actual == 'subir':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_subir_total = tiempo_movimiento
                            limite_superior_marcado = True
                            print(f"\n✅ LÍMITE SUPERIOR marcado: {tiempo_movimiento:.2f}s desde inicio")
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                        else:
                            print("\n⚠️  Debes estar SUBIENDO para marcar límite superior")
                    
                    elif tecla == 'n':
                        if estado_actual == 'bajar':
                            tiempo_movimiento = time.time() - tiempo_inicio_movimiento
                            tiempo_bajar_total = tiempo_movimiento
                            limite_inferior_marcado = True
                            print(f"\n✅ LÍMITE INFERIOR marcado: {tiempo_movimiento:.2f}s desde inicio")
                            aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                            estado_actual = 'detenido'
                        else:
                            print("\n⚠️  Debes estar BAJANDO para marcar límite inferior")
                    
                    elif tecla == 'q':
                        print("\n\n💾 Guardando datos de aprendizaje...")
                        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                        break
                
                else:
                    # No hay tecla presionada - DETENER
                    if estado_actual != 'detenido':
                        if estado_actual == 'subir' and tiempo_inicio_movimiento:
                            tiempo_subir_total += time.time() - tiempo_inicio_movimiento
                        elif estado_actual == 'bajar' and tiempo_inicio_movimiento:
                            tiempo_bajar_total += time.time() - tiempo_inicio_movimiento
                        
                        print(f"\r⏹️  DETENIDO        ", end='', flush=True)
                        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)
                        estado_actual = 'detenido'
                        tiempo_inicio_movimiento = None
                
                time.sleep(0.02)  # 50Hz actualización
        
        # Guardar datos aprendidos
        datos_aprendidos = {
            "timestamp": datetime.now().isoformat(),
            "servo": "hombro",
            "canal": CANAL_HOMBRO,
            "pulso_neutral": PULSO_NEUTRAL,
            "pulso_subir": PULSO_SUBIR,
            "pulso_bajar": PULSO_BAJAR,
            "limites": {
                "superior_marcado": limite_superior_marcado,
                "inferior_marcado": limite_inferior_marcado,
                "tiempo_subir_max": round(tiempo_subir_total, 2),
                "tiempo_bajar_max": round(tiempo_bajar_total, 2)
            },
            "observaciones": {
                "detiene_correctamente": True,  # Actualizar según tu prueba
                "velocidad_adecuada": True,
                "suavidad_movimiento": True
            }
        }
        
        # Guardar a archivo
        with open('aprendizaje_hombro.json', 'w') as f:
            json.dump(datos_aprendidos, f, indent=2)
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE APRENDIZAJE")
        print("="*60)
        print(f"\n🔧 CONFIGURACIÓN:")
        print(f"  • Pulso neutral: {PULSO_NEUTRAL}µs")
        print(f"  • Pulso subir: {PULSO_SUBIR}µs")
        print(f"  • Pulso bajar: {PULSO_BAJAR}µs")
        print(f"\n📏 LÍMITES FÍSICOS:")
        print(f"  • Tiempo máximo SUBIR: {tiempo_subir_total:.2f}s")
        print(f"  • Tiempo máximo BAJAR: {tiempo_bajar_total:.2f}s")
        print(f"  • Límite superior marcado: {'✅' if limite_superior_marcado else '❌'}")
        print(f"  • Límite inferior marcado: {'✅' if limite_inferior_marcado else '❌'}")
        print(f"\n💾 Datos guardados en: aprendizaje_hombro.json")
        print("="*60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupción")
        aplicar_pulso(pca, CANAL_HOMBRO, PULSO_NEUTRAL)

if __name__ == '__main__':
    main()
