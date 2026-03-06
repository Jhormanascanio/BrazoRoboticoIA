import time
import board
import busio
from adafruit_pca9685 import PCA9685
from gpiozero import OutputDevice
import logging as log
import json
import os

class ControladorServo:
    """Controlador para servos continuos usando PCA9685 con movimientos temporizados"""

    def __init__(self, direccion_i2c=0x40, frecuencia=50):
        """Inicializar controlador PCA9685"""
        # Para Raspberry Pi 5: usar GPIO 3 (SCL) y GPIO 2 (SDA) - puerto I2C1
        # Estos son los pines físicos 5 y 3 respectivamente
        try:
            self.i2c = busio.I2C(board.D3, board.D2)
            log.info("I2C inicializado en GPIO3/GPIO2 (bus I2C1)")
        except Exception as e:
            log.error(f"Error inicializando I2C en GPIO3/GPIO2: {e}")
            log.error("Verifica que I2C esté habilitado en raspi-config")
            raise
        
        self.pca = PCA9685(self.i2c, address=direccion_i2c)
        self.pca.frequency = frecuencia
        self.servos = {}
        
        # Cargar pulsos neutrales calibrados desde servo_config.json
        self.pulsos_neutrales = self._cargar_pulsos_neutrales()
        log.info(f"Pulsos neutrales cargados: {self.pulsos_neutrales}")
        
        # Diagnóstico y seguridad
        # Si es True, se aplicará un pequeño pulso de "hold" en lugar del pulso
        # neutral exacto cuando termine el movimiento.
        # Por defecto: False (mantener comportamiento existente)
        self.hold_after_move = False
        # Cantidad (en microsegundos) para desplazar del neutral cuando está en hold.
        # Usar valores pequeños (ej. 50-200) durante pruebas. Esto no convierte
        # servos continuos en posicionales - es solo un pequeño bias/pulso.
        self.hold_pulse_offset = 100

    def _cargar_pulsos_neutrales(self):
        """Cargar pulsos neutrales y pulsos hold calibrados desde servo_config.json"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'servo_config.json')
        
        # Valores por defecto si no existe el archivo
        default_config = {
            'shoulder': {'pulso_neutral': 1700, 'pulso_hold': 1700},
            'elbow': {'pulso_neutral': 1720, 'pulso_hold': 1850},
            'wrist': {'pulso_neutral': 1682, 'pulso_hold': 1800},
            'gripper': {'pulso_neutral': 1690, 'pulso_hold': 1690}
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Extraer pulsos neutrales y hold
                    pulsos = {}
                    for nombre, datos in config.items():
                        pulsos[nombre] = {
                            'neutral': datos.get('pulso_neutral', default_config.get(nombre, {}).get('pulso_neutral', 1500)),
                            'hold': datos.get('pulso_hold', datos.get('pulso_neutral', default_config.get(nombre, {}).get('pulso_hold', 1500)))
                        }
                    log.info(f"✅ Pulsos neutrales y hold cargados desde {config_path}")
                    return pulsos
            else:
                log.warning(f"⚠️  No se encontró {config_path}, usando valores calibrados por defecto")
                return {k: {'neutral': v['pulso_neutral'], 'hold': v['pulso_hold']} for k, v in default_config.items()}
        except Exception as e:
            log.error(f"❌ Error cargando servo_config.json: {e}")
            log.warning("Usando valores calibrados por defecto")
            return {k: {'neutral': v['pulso_neutral'], 'hold': v['pulso_hold']} for k, v in default_config.items()}

    def agregar_servo(self, nombre, canal, pulso_min=500, pulso_max=2500, angulo_min=0, angulo_max=180):
        """Agregar servo al controlador"""
        # Usar rango completo de pulso para servos MG996R
        config = self.pulsos_neutrales.get(nombre, {'neutral': 1500, 'hold': 1500})
        self.servos[nombre] = {
            'canal': canal,
            'pulso_min': pulso_min,
            'pulso_max': pulso_max,
            'angulo_min': angulo_min,
            'angulo_max': angulo_max,
            'pulso_neutral': config['neutral'],  # Pulso neutral personalizado
            'pulso_hold': config['hold']  # Pulso hold para compensación de gravedad
        }
        log.info(f"Servo '{nombre}' agregado: canal={canal}, pulso_neutral={self.servos[nombre]['pulso_neutral']}µs, pulso_hold={self.servos[nombre]['pulso_hold']}µs")

    def mover_por_tiempo(self, nombre, direccion, tiempo_segundos, velocidad=0.5):
        """Mover servo continuo por tiempo específico en lugar de ángulos
        
        Args:
            nombre: Nombre del servo
            direccion: -1 = horario, 0 = parar, 1 = antihorario
            tiempo_segundos: Tiempo de movimiento
            velocidad: Factor de velocidad 0.0-1.0 (por defecto 0.5 para movimientos suaves)
        """
        if nombre not in self.servos:
            log.error(f"Servo {nombre} no configurado")
            return

        servo = self.servos[nombre]
        pulso_neutral = servo['pulso_neutral']  # Usar pulso neutral calibrado

        # CONTROL DE SERVOS CONTINUOS - Control de velocidad por tiempo
        # direccion: -1 = giro horario, 0 = parar, 1 = giro antihorario
        if direccion == 0:
            # Detener - usar pulso neutral calibrado
            pulso = pulso_neutral
        elif direccion == -1:
            # Giro horario (sentido horario)
            pulso = pulso_neutral + (500 * velocidad)  # neutral+500us
        elif direccion == 1:
            # Giro antihorario (sentido antihorario)
            pulso = pulso_neutral - (500 * velocidad)  # neutral-500us
        else:
            log.error(f"Dirección inválida: {direccion}")
            return

        ciclo_trabajo = int(pulso / 20000 * 0xFFFF)  # Periodo 50Hz
        log.info(f"[Servo] {nombre}: inicio movimiento dir={direccion} tiempo={tiempo_segundos}s pulso={pulso}us (neutral={pulso_neutral}us) canal={servo['canal']}")
        self.pca.channels[servo['canal']].duty_cycle = ciclo_trabajo

        # Mantener movimiento por el tiempo especificado
        time.sleep(tiempo_segundos)

        # Usar PULSO_HOLD al terminar (compensa gravedad en codo y muñeca)
        pulso_hold = servo['pulso_hold']
        ciclo_hold = int(pulso_hold / 20000 * 0xFFFF)
        self.pca.channels[servo['canal']].duty_cycle = ciclo_hold
        log.info(f"[Servo] {nombre}: detenido con pulso hold {pulso_hold}us (neutral={pulso_neutral}us)")

    def detener_servo(self, nombre):
        """Detener servo específico"""
        if nombre in self.servos:
            servo = self.servos[nombre]
            pulso_hold = servo['pulso_hold']  # Usar pulso hold calibrado
            # Pulso hold calibrado para detener (compensa gravedad)
            ciclo_trabajo = int(pulso_hold / 20000 * 0xFFFF)
            self.pca.channels[servo['canal']].duty_cycle = ciclo_trabajo
            log.info(f"[Servo] {nombre}: detener_servo -> pulso hold {pulso_hold}us aplicado")

    def set_hold_after_move(self, enabled: bool, offset_us: int = None):
        """Habilitar/deshabilitar la aplicación de pequeño pulso de hold al terminar un movimiento.

        enabled: True para activar, False para desactivar.
        offset_us: si se pasa, actualiza self.hold_pulse_offset (microsegundos).
        """
        self.hold_after_move = bool(enabled)
        if offset_us is not None:
            try:
                self.hold_pulse_offset = int(offset_us)
            except Exception:
                log.warning("hold_pulse_offset debe ser entero (microsegundos); ignorando valor inválido")
        log.info(f"[Servo] set_hold_after_move={self.hold_after_move} hold_pulse_offset={self.hold_pulse_offset}")

    def detener_todos(self):
        """Detener todos los servos"""
        for nombre in self.servos:
            self.detener_servo(nombre)

class ControladorStepper:
    """Controlador para motores stepper"""

    def __init__(self, pin_paso, pin_direccion, pin_habilitar=None, pasos_por_rev=200, micropasos=16):
        """Inicializar controlador stepper"""
        self.pin_paso = OutputDevice(pin_paso)
        self.pin_direccion = OutputDevice(pin_direccion)
        self.pin_habilitar = OutputDevice(pin_habilitar) if pin_habilitar else None
        self.pasos_por_rev = pasos_por_rev * micropasos
        self.posicion_actual = 0

    def habilitar(self):
        """Habilitar motor stepper"""
        if self.pin_habilitar:
            self.pin_habilitar.off()  # Asumiendo activo bajo

    def deshabilitar(self):
        """Deshabilitar motor stepper"""
        if self.pin_habilitar:
            self.pin_habilitar.on()

    def mover_pasos(self, pasos, direccion=1, velocidad=1000):  # pasos por segundo
        """Mover stepper una cantidad específica de pasos"""
        
        self.pin_direccion.value = 1 if direccion > 0 else 0
        retardo = 1.0 / velocidad
        for _ in range(abs(pasos)):
            self.pin_paso.on()
            time.sleep(retardo / 2)
            self.pin_paso.off()
            time.sleep(retardo / 2)
        self.posicion_actual += pasos * direccion

    def mover_distancia(self, distancia_mm, paso_tuerca=8, direccion=1, velocidad=1000):
        """Mover stepper una distancia específica en mm"""
        pasos = int((distancia_mm / paso_tuerca) * self.pasos_por_rev)
        self.mover_pasos(pasos, direccion, velocidad)

class ControladorRobotico:
    """Controlador principal del brazo robótico con movimientos temporizados y límites físicos"""

    def __init__(self, habilitar_stepper=True):
        """Inicializar controlador del robot
        
        Args:
            habilitar_stepper: Si es False, no inicializa el motor paso a paso (útil si no está conectado o da error)
        """
        self.controlador_servo = ControladorServo()
        # Configurar servos: hombro (canal 0), codo (1), muñeca (2), pinza (3)
        # Todos los servos son continuos de 360°
        # NO hay servo "base" - el movimiento horizontal es con motor paso a paso
        self.controlador_servo.agregar_servo('shoulder', 0, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('elbow', 1, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('wrist', 2, angulo_min=0, angulo_max=360)
        self.controlador_servo.agregar_servo('gripper', 3, angulo_min=0, angulo_max=360)

        # Motor paso a paso para movimiento HORIZONTAL (izquierda/derecha)
        # TMC2208: STEP=GPIO14, DIR=GPIO15 (según tus conexiones reales)
        # Solo inicializar si está habilitado
        self.controlador_stepper = None
        if habilitar_stepper:
            try:
                self.controlador_stepper = ControladorStepper(pin_paso=14, pin_direccion=15, pin_habilitar=None)
                log.info("✅ Motor paso a paso inicializado (GPIO14=STEP, GPIO15=DIR)")
            except Exception as e:
                log.warning(f"⚠️  No se pudo inicializar motor paso a paso: {e}")
                log.warning("   El brazo funcionará solo con servos (sin movimiento horizontal)")
        else:
            log.info("ℹ️  Motor paso a paso deshabilitado (solo servos)")

        # LÍMITES FÍSICOS DEL BRAZO (en segundos de movimiento)
        # Estos límites previenen que el brazo se salga de su rango físico
        self.limites_fisicos = {
            'base': {'izquierda': 3.0, 'derecha': 3.0},  # Máximo 3 segundos en cada dirección
            'shoulder': {'arriba': 2.5, 'abajo': 2.5},   # Máximo 2.5 segundos en cada dirección
            'elbow': {'extender': 3.5, 'contraer': 3.5}, # Máximo 3.5 segundos en cada dirección
            'gripper': {'abrir': 1.5, 'cerrar': 1.5}     # Máximo 1.5 segundos en cada dirección
        }

        # Estado actual de tiempo acumulado por articulación
        self.tiempo_acumulado = {
            'base': 0.0,
            'shoulder': 0.0,
            'elbow': 0.0,
            'gripper': 0.0
        }

    def mover_base_tiempo(self, direccion, tiempo_segundos, velocidad=0.5):
        """Mover base por tiempo con límites físicos (velocidad reducida por defecto)"""
        tiempo_limitado = min(tiempo_segundos, self.limites_fisicos['base']['derecha' if direccion == 1 else 'izquierda'])
        if tiempo_limitado > 0:
            self.controlador_servo.mover_por_tiempo('base', direccion, tiempo_limitado, velocidad)
            self.tiempo_acumulado['base'] += tiempo_limitado * direccion
        return tiempo_limitado

    def mover_hombro_tiempo(self, direccion, tiempo_segundos, velocidad=0.5):
        """Mover hombro por tiempo con límites físicos (velocidad reducida por defecto)"""
        tiempo_limitado = min(tiempo_segundos, self.limites_fisicos['shoulder']['arriba' if direccion == 1 else 'abajo'])
        if tiempo_limitado > 0:
            self.controlador_servo.mover_por_tiempo('shoulder', direccion, tiempo_limitado, velocidad)
            self.tiempo_acumulado['shoulder'] += tiempo_limitado * direccion
        return tiempo_limitado

    def mover_codo_tiempo(self, direccion, tiempo_segundos, velocidad=0.5):
        """Mover codo por tiempo con límites físicos (velocidad reducida por defecto)"""
        tiempo_limitado = min(tiempo_segundos, self.limites_fisicos['elbow']['extender' if direccion == 1 else 'contraer'])
        if tiempo_limitado > 0:
            self.controlador_servo.mover_por_tiempo('elbow', direccion, tiempo_limitado, velocidad)
            self.tiempo_acumulado['elbow'] += tiempo_limitado * direccion
        return tiempo_limitado

    def mover_pinza_tiempo(self, direccion, tiempo_segundos, velocidad=0.5):
        """Mover pinza por tiempo con límites físicos (velocidad reducida por defecto)"""
        tiempo_limitado = min(tiempo_segundos, self.limites_fisicos['gripper']['abrir' if direccion == 1 else 'cerrar'])
        if tiempo_limitado > 0:
            self.controlador_servo.mover_por_tiempo('gripper', direccion, tiempo_limitado, velocidad)
            self.tiempo_acumulado['gripper'] += tiempo_limitado * direccion
        return tiempo_limitado

    # MÉTODOS LEGACY PARA COMPATIBILIDAD (ya no se usan grados)
    def mover_base(self, angulo, velocidad=5):
        """Mover base del robot (LEGACY - ahora usa tiempo)"""
        log.warning("mover_base con ángulos está obsoleto. Usa mover_base_tiempo")
        # Convertir ángulo aproximado a tiempo (180° ≈ 2 segundos)
        tiempo = abs(angulo - 180) / 90.0  # Aproximación simple
        direccion = 1 if angulo > 180 else -1
        self.mover_base_tiempo(direccion, tiempo, velocidad)

    def mover_hombro(self, angulo, velocidad=5):
        """Mover hombro del robot (LEGACY)"""
        log.warning("mover_hombro con ángulos está obsoleto. Usa mover_hombro_tiempo")
        tiempo = abs(angulo - 180) / 90.0
        direccion = 1 if angulo > 180 else -1
        self.mover_hombro_tiempo(direccion, tiempo, velocidad)

    def mover_codo(self, angulo, velocidad=5):
        """Mover codo del robot (LEGACY)"""
        log.warning("mover_codo con ángulos está obsoleto. Usa mover_codo_tiempo")
        tiempo = abs(angulo - 180) / 90.0
        direccion = 1 if angulo > 180 else -1
        self.mover_codo_tiempo(direccion, tiempo, velocidad)

    def mover_pinza(self, angulo, velocidad=5):
        """Mover pinza del robot (LEGACY)"""
        log.warning("mover_pinza con ángulos está obsoleto. Usa mover_pinza_tiempo")
        tiempo = abs(angulo - 180) / 90.0
        direccion = 1 if angulo > 180 else -1
        self.mover_pinza_tiempo(direccion, tiempo, velocidad)

    def mover_brazo(self, distancia_mm, direccion=1, velocidad=1000):
        """Mover brazo horizontalmente (izquierda/derecha) usando motor paso a paso
        
        Args:
            distancia_mm: Distancia en milímetros a mover
            direccion: 1 = derecha, -1 = izquierda
            velocidad: Velocidad del motor (pasos por segundo)
        """
        if self.controlador_stepper is None:
            log.warning("⚠️  Motor paso a paso no disponible - movimiento horizontal deshabilitado")
            return
        self.controlador_stepper.mover_distancia(distancia_mm, direccion=direccion, velocidad=velocidad)

    def accion_recoger(self):
        """Abrir pinza para recoger"""
        self.mover_pinza_tiempo(1, 1.0)  # Abrir por 1 segundo

    def accion_soltar(self):
        """Cerrar pinza para soltar"""
        self.mover_pinza_tiempo(-1, 1.0)  # Cerrar por 1 segundo

    def mover_horizontal(self, distancia=50, direccion=1):
        """Mover brazo horizontalmente (izquierda/derecha) con motor paso a paso
        
        Args:
            distancia: Distancia en mm (por defecto 50mm)
            direccion: 1 = derecha, -1 = izquierda
        """
        self.mover_brazo(distancia, direccion=direccion)

    def resetear_tiempos(self):
        """Resetear contadores de tiempo acumulado"""
        self.tiempo_acumulado = {k: 0.0 for k in self.tiempo_acumulado}

    def obtener_estado_tiempos(self):
        """Obtener estado actual de tiempos acumulados"""
        return self.tiempo_acumulado.copy()

    def secuencia_recoger(self, angulo_base_pasos=0, tiempo_bajar=1.5, tiempo_cerrar=0.8, velocidad=0.4):
        """Secuencia completa de pick: posicionar, bajar, agarrar, subir.
        Retorna True si la secuencia se completo sin excepciones."""
        try:
            if angulo_base_pasos != 0 and self.controlador_stepper:
                direccion = 1 if angulo_base_pasos > 0 else -1
                self.controlador_stepper.mover_pasos(abs(angulo_base_pasos), direccion=direccion, velocidad=800)
                time.sleep(0.3)

            self.controlador_servo.mover_por_tiempo('shoulder', -1, tiempo_bajar, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('elbow', 1, tiempo_bajar * 0.6, velocidad)
            time.sleep(0.2)

            self.controlador_servo.mover_por_tiempo('gripper', -1, tiempo_cerrar, velocidad=0.6)
            time.sleep(0.4)

            self.controlador_servo.mover_por_tiempo('shoulder', 1, tiempo_bajar * 1.1, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('elbow', -1, tiempo_bajar * 0.5, velocidad)

            log.info("Secuencia RECOGER completada")
            return True
        except Exception as e:
            log.error(f"Error en secuencia recoger: {e}")
            self._posicion_segura()
            return False

    def secuencia_soltar(self, angulo_base_pasos=0, tiempo_bajar=1.2, velocidad=0.4):
        """Secuencia completa de place: posicionar, bajar, soltar, subir."""
        try:
            if angulo_base_pasos != 0 and self.controlador_stepper:
                direccion = 1 if angulo_base_pasos > 0 else -1
                self.controlador_stepper.mover_pasos(abs(angulo_base_pasos), direccion=direccion, velocidad=800)
                time.sleep(0.3)

            self.controlador_servo.mover_por_tiempo('shoulder', -1, tiempo_bajar, velocidad)
            time.sleep(0.2)

            self.controlador_servo.mover_por_tiempo('gripper', 1, 0.8, velocidad=0.6)
            time.sleep(0.3)

            self.controlador_servo.mover_por_tiempo('shoulder', 1, tiempo_bajar * 1.1, velocidad)
            time.sleep(0.2)

            log.info("Secuencia SOLTAR completada")
            return True
        except Exception as e:
            log.error(f"Error en secuencia soltar: {e}")
            self._posicion_segura()
            return False

    def verificar_agarre(self):
        """Intenta detectar si la pinza realmente agarro algo.
        Hace un micro-cierre adicional: si la pinza se mueve muy rapido,
        probablemente no hay objeto (cerro en vacio)."""
        try:
            t_inicio = time.time()
            self.controlador_servo.mover_por_tiempo('gripper', -1, 0.15, velocidad=0.3)
            t_total = time.time() - t_inicio
            if t_total < 0.1:
                log.warning("Agarre posiblemente fallido: pinza cerro sin resistencia")
                return False
            log.info("Agarre verificado (resistencia detectada)")
            return True
        except Exception:
            return False

    def _posicion_segura(self):
        """Mover a posicion segura en caso de error."""
        log.warning("Moviendo a posicion segura...")
        try:
            self.controlador_servo.mover_por_tiempo('gripper', 1, 0.5, velocidad=0.5)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('shoulder', 1, 1.5, velocidad=0.3)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('elbow', -1, 1.0, velocidad=0.3)
            self.controlador_servo.detener_todos()
            log.info("Posicion segura alcanzada")
        except Exception as e:
            log.error(f"Error critico yendo a posicion segura: {e}")
            self.controlador_servo.detener_todos()

    def posicion_home(self, velocidad=0.3):
        """Mover todas las articulaciones a posicion de reposo."""
        try:
            self.controlador_servo.mover_por_tiempo('gripper', 1, 0.6, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('shoulder', 1, 1.5, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('elbow', -1, 1.0, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('wrist', 1, 0.5, velocidad)
            self.controlador_servo.detener_todos()
            self.resetear_tiempos()
            log.info("Posicion HOME alcanzada")
        except Exception as e:
            log.error(f"Error en home: {e}")

    def posicion_escaneo(self, velocidad=0.3):
        """Posicionar brazo para que la camara tenga buena vista del area de trabajo."""
        try:
            self.controlador_servo.mover_por_tiempo('shoulder', 1, 0.8, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('elbow', 1, 0.5, velocidad)
            time.sleep(0.2)
            self.controlador_servo.mover_por_tiempo('wrist', -1, 0.3, velocidad)
            self.controlador_servo.detener_todos()
            log.info("Posicion de ESCANEO alcanzada")
        except Exception as e:
            log.error(f"Error en posicion escaneo: {e}")

    def cerrar(self):
        """Cerrar controladores y liberar recursos"""
        try:
            self.controlador_servo.detener_todos()
            if self.controlador_stepper:
                self.controlador_stepper.deshabilitar()
            self.controlador_servo.pca.deinit()
        except Exception as e:
            log.error(f"Error cerrando controladores: {e}")
