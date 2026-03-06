# CONFIGURACIÓN DEL SISTEMA - Brazo Robótico
# Este archivo controla qué componentes están habilitados

# SERVOS (PCA9685) - Todos calibrados y funcionando
SERVOS_HABILITADOS = True

# MOTOR PASO A PASO (TMC2208) - Habilitado (cables corregidos)
STEPPER_HABILITADO = True

# CÁMARA
CAMARA_HABILITADA = True

# Servos: Hombro(0), Codo(1), Muñeca(2), Pinza(3)
# Stepper NEMA 17: rotacion de base horizontal via TMC2208

# Configuracion del modo autonomo
MODO_AUTONOMO = True
COLORES_RECIPIENTES = {
    'rojo': {'h_min': 0, 'h_max': 10, 's_min': 100, 'v_min': 100},
    'azul': {'h_min': 100, 'h_max': 130, 's_min': 100, 'v_min': 100},
    'verde': {'h_min': 40, 'h_max': 80, 's_min': 100, 'v_min': 100},
    'amarillo': {'h_min': 20, 'h_max': 35, 's_min': 100, 'v_min': 100},
}
CONFIANZA_MINIMA_DETECCION = 0.45
MAX_REINTENTOS_AGARRE = 3
VELOCIDAD_AUTONOMA = 0.4
