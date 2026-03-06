# Automatic Zoom
## 2025

# Curso de Robótica: Visión, control e inteligencia artificial.

**Desarrollado por:**  
Harol Camilo Melo Torrado  
Estudiante de Ingeniería de Sistemas  
Universidad Francisco de Paula Santander Ocaña (UFPSO)

Este curso integral explora el desarrollo de un sistema de brazo robótico inteligente, desde conceptos fundamentales hasta implementaciones avanzadas. Se ha construido un sistema de brazo robótico completo capaz de escanear el entorno, detectar objetos y realizar manipulaciones autónomas mediante visión artificial, cinemática, control por voz y modelos de lenguaje de gran tamaño.

# Nivel 1. Fundamentos básicos de robótica y visión artificial.

## Descripción del curso

### Módulo 1: Arquitectura y configuración del sistema
- Introducción y descripción general del sistema
- Hoja de ruta y objetivos del curso
- Componentes de hardware (Raspberry Pi 5, VEX IQ)
- Fundamentos de la arquitectura maestro-esclavo
- Descripción general de los servicios del sistema
- Diseño del sistema
- Fundamentos y arquitectura modular
- Diagrama de flujo del sistema
- Comunicación entre módulos
- Diseño de protocolos de comunicación
- Protocolos de comunicación
- Fundamentos de la comunicación serial
- Implementación de la comunicación serial
- Diseño de un protocolo robusto basado en JSON

### Módulo 2: Movimiento básico y control
- Fundamentos básicos de movimiento del motor
- Fundamentos del control del motor
- Sistemas de control conjunto
- Secuencias de movimiento
- Implementación de servicios básicos de movimiento
- Servicio básico de posición segura
- Servicio básico de escaneo y percepción del entorno
- Servicio básico de pick & place

### Módulo 3: Visión artificial básica
- Introducción a la visión artificial
- Fundamentos de la visión artificial
- Conexión de cámaras a la Raspberry PI
- Fundamentos de la detección de objetos
- Introducción a la detección de objetos
- Introducción a la arquitectura YOLO
- Configuración de modelos preentrenados
- Inferencia básica YOLO
- Conversión de modelos
- Identificación de objetos
- Captura de imágenes
- Conceptos básicos de procesamiento y visualización
- Dibujar y guardar resultados

### Módulo 4: Integración del sistema
- Proyecto final
- Integración de todos los servicios
- Construcción del sistema básico completo
- Demostración de capacidades básicas
- Identificación de fallos y posibles mejoras
- Evaluación del desempeño

## Hardware VEX IQ

### Articulaciones y Juntas Cinemáticas

Las articulaciones en robótica son los puntos de conexión que permiten el movimiento relativo entre dos partes de un robot. Las juntas cinemáticas describen cómo estas articulaciones facilitan el movimiento en términos de grados de libertad (DOF, por sus siglas en inglés), que indican las direcciones independientes en las que un componente puede moverse. En el caso del Armbot IQ, un robot educativo con un brazo robótico, las articulaciones son esenciales para permitir que el brazo y la garra se desplacen y manipulen objetos.

#### Tipos de Articulaciones

**Articulaciones Rotativas:**
- Permiten la rotación alrededor de un eje
- En el Armbot IQ se utilizan para:
  - Girar la base del brazo en el plano horizontal
  - Girar el hombro para extender el brazo
  - Girar el "codo" del brazo para elevar o bajar la garra
- Son comunes por su simplicidad y versatilidad

**Articulaciones Prismáticas:**
- Permiten el movimiento lineal a lo largo de un eje
- Menos frecuentes en robots pequeños como VEX IQ
- Potencial uso en extensiones lineales del brazo en diseños avanzados

### Relación de Engranajes

Los engranajes son componentes fundamentales que transmiten el movimiento y la fuerza desde los motores a las articulaciones y la garra.

#### Cálculo de Relación de Engranajes
- Fórmula: Relación = Número de dientes del engranaje conducido / Número de dientes del engranaje conductor
- Ejemplo:
  - Engranaje conductor: 12 dientes
  - Engranaje conducido: 36 dientes
  - Relación = 36/12 = 3:1
  - Resultado: El engranaje conductor debe girar tres veces para una vuelta del conducido

#### Aplicación en el Armbot IQ

**Reducción de Velocidad y Aumento de Torque:**
- Disminución de velocidad de motores
- Aumento de torque para levantar cargas pesadas
- Ejemplo: Relación 5:1 en el codo para mayor fuerza

**Cadena de Engranajes:**
- Serie de engranajes conectados
- Logra la relación deseada entre motor y articulación

### Otros Aspectos Mecánicos

#### Estructura y Materiales
- Chasis y partes en plástico resistente
- Diseño ligero pero duradero
- Sistema modular con pines y conectores

#### Mecanismos de Transmisión
- Engranajes como método principal
- Ejes metálicos para rigidez y precisión
- Predominio de engranajes sobre correas o cadenas

## Arquitectura Detallada del Sistema

### Módulo Principal
El orquestador central del sistema que gestiona la interacción y coordinación.

**Funciones Principales:**
- `main_menu_loop`: Menú interactivo con opciones de operación
- `handle_scan_command`: Gestión del servicio de escaneo
- `handle_pick_place_command`: Ejecución de pick & place
- `process_scan_results`: Procesamiento de resultados de escaneo
- `select_object_interactively`: Selección interactiva de objetos
- `execute_pick_sequence`: Secuencia de recogida
- `execute_place_sequence`: Secuencia de colocación
- `get_current_angles`: Obtención de ángulos actuales
- `execute_movement`: Ejecución de comandos de movimiento
- `handle_movement_failure`: Gestión de fallos

### Módulo de Comunicación
Gestiona la comunicación serial entre el sistema y el hardware.

**Clase Robot:**
- `connect`: Conexión serial
- `close`: Cierre de conexión
- `send_message`: Envío de mensajes JSON
- `register_callback`: Registro de callbacks
- `_read_loop`: Lectura continua de mensajes
- `_process_message`: Procesamiento de mensajes
- `_handle_object_detection`: Gestión de detección
- `get_scan_data`: Obtención de datos de escaneo
- `wait_for_confirmation`: Espera de confirmaciones
- `wait_for_angles_response`: Espera de respuesta de ángulos

### Módulo de Percepción
Sistema de visión artificial y procesamiento de imágenes.

**CameraManager:**
- `capture_image`: Captura y almacenamiento de imágenes

**ImageProcessor:**
- `read_image_path`: Lectura y detección en imágenes
- `process_image`: Procesamiento con YOLO
- `_draw_detection`: Visualización de detecciones
- `_save_drawn_image`: Almacenamiento de resultados

### Módulo de Control del Brazo
Control directo de motores y sensores en VEX Brain.

**CommunicationManager (VEX):**
- `initialize`: Inicialización de comunicación
- `read_message`: Lectura de mensajes
- `send_message`: Envío de mensajes

**SensorModule:**
- `clear_screen`: Limpieza de pantalla
- `print_screen`: Impresión en pantalla
- `get_angle`: Lectura de ángulos
- `get_distance`: Medición de distancia
- `get_object_size`: Detección de tamaño
- `is_bumper_pressed`: Estado del bumper
- `set_color`: Control de indicadores LED
- `check_sensors`: Verificación de sensores

**ControlModule:**
- `move_motor_to_angle`: Control de motores
- `get_position`: Lectura de posición
- `get_current`: Monitoreo de corriente
- `general_stop`: Parada de emergencia
- `check_motors`: Verificación de motores

**SafetyModule:**
- `check_motors`: Verificación de motores
- `check_sensors`: Verificación de sensores
- `check_shoulder_safety`: Seguridad del hombro
- `gripper_action`: Control seguro del gripper

## Estructura del Proyecto

```
arm_system/
├── ai/              # Módulos de IA y ML
├── communication/   # Gestión de comunicaciones
├── control/         # Control del robot
├── mapping/         # Sistema de mapeo
├── perception/      # Procesamiento de visión
├── planning/        # Planificación de movimientos
├── ui/             # Interfaz de usuario
├── voice/          # Control por voz
└── vex_brain/      # Control del VEX IQ
```

## Tecnologías Implementadas

- Python para el control principal
- YOLO para detección de objetos
- OpenCV para procesamiento de imágenes
- JSON para comunicación entre módulos
- PyTorch para modelos de IA
- Protocolos seriales para comunicación con VEX IQ

## Contribuciones y Mejoras

Este proyecto representa una implementación completa y funcional de un sistema robótico inteligente, con énfasis en:
- Integración de IA para toma de decisiones
- Sistema de visión artificial robusto
- Control preciso y seguro del brazo robótico
- Interfaz de usuario amigable
- Documentación detallada del sistema

---
© 2025 Harol Camilo Melo Torrado - UFPSO