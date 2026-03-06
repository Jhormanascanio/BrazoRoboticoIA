o# Brazo Robótico Autónomo con Visión Artificial

Este repositorio guía en la construcción paso a paso de un brazo robótico autónomo con visión artificial, desde el nivel principiante. Incluye control de servomotores y motor paso a paso, detección de objetos con YOLO, y operación autónoma de pick & place.

## Componentes Hardware

- **Raspberry Pi 5** (2GB RAM) - Controlador principal
- **Servos MG996R** (4 unidades): base, hombro, codo, pinza
- **Motor NEMA 17** con reductor - Elevación del brazo
- **PCA9685** - Controlador I2C para servos (16 canales)
- **TMC2208** - Driver SilentStepStick para NEMA 17
- **Raspberry Pi Camera** - Visión artificial
- **Fuentes de alimentación**:
  - 5V/20A para servos
  - 12V/5A para NEMA 17 + TMC2208

## Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd BrazoRoboticoConIA
cd definitivo
```

### 2. Configurar hardware (Opcional - para modo completo)

#### Conexiones PCA9685 (Servos)
- **VCC**: 5V (desde Raspberry Pi)
- **GND**: GND (desde Raspberry Pi)
- **SDA**: Pin 3 (GPIO 2)
- **SCL**: Pin 5 (GPIO 3)
- **Canales**:
  - Canal 0: Servo base
  - Canal 1: Servo hombro
  - Canal 2: Servo codo
  - Canal 3: Servo pinza

#### Conexiones TMC2208 (Motor paso a paso)
- **VM**: 12V (fuente externa)
- **GND**: GND (común)
- **STEP**: GPIO 17 (Pin 11)
- **DIR**: GPIO 18 (Pin 12)
- **ENABLE**: GPIO 19 (Pin 35) - Opcional

#### Cámara Raspberry Pi
- Conectar al puerto CSI de la Raspberry Pi
- Ejecutar: `sudo raspi-config` → Interfacing Options → Camera → Enable

### 3. Crear y activar entorno virtual
```bash
# Instalar Python y herramientas de desarrollo
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-opencv \
    python3-setuptools \
    build-essential

# Crear el entorno virtual con Python
python3 -m venv venv --system-site-packages

# Activar el entorno virtual
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate     # En Windows
```

### 3. Instalar dependencias del sistema

#### Para Windows:
1. Instalar Python desde [python.org](https://www.python.org/downloads/)
2. Instalar Git desde [git-scm.com](https://git-scm.com/download/win)
3. Instalar Visual Studio Build Tools (necesario para algunas dependencias):
   - Descargar desde [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - En el instalador, seleccionar "Desktop development with C++"
4. Instalar OpenCV:
```bash
pip install opencv-python
```

#### Para Raspberry Pi (Ubuntu/Debian):
```bash
# En Ubuntu/Debian (necesario para la Raspberry Pi)
sudo apt update
sudo apt install -y python3-dev python3-setuptools python3-pip python3-smbus build-essential git i2c-tools python3-rpi.gpio python3-lgpio python3-gpiozero libopencv-dev python3-opencv ffmpeg libxml2-dev libxslt1-dev libdbus-1-dev libglib2.0-dev pkg-config cmake gcc g++ wget

# Para Raspberry Pi 5, configurar GPIO usando lgpio (recomendado)
# Paso 1: Instalar las dependencias de GPIO
sudo apt update
sudo apt install -y python3-lgpio

# Paso 2: Configurar permisos
sudo usermod -a -G gpio $USER    # Agregar usuario al grupo gpio

# Paso 3: Verificar la instalación de lgpio
python3 -c "import lgpio; print('LGPIO instalado correctamente')"

# Nota: Para Raspberry Pi 5, lgpio es la biblioteca recomendada y nativa
# No se requiere ningún servicio adicional para usar lgpio

# Habilitar I2C y la cámara
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0

# Agregar usuario al grupo i2c y video
sudo usermod -a -G i2c,video $USER
```

### 4. Instalar dependencias de Python
```bash
# Actualizar pip e instalar todas las dependencias
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# En Raspberry Pi, agregar el índice piwheels para optimizar la instalación
if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "armv7l" ]; then
    pip config set global.extra-index-url https://www.piwheels.org/simple
fi

# Verificar la instalación
python -c "import cv2; import ultralytics; print('Instalación exitosa')"
```

### 5. Solución de problemas comunes

#### Error de compatibilidad con Python 3.13
Si encuentras `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`:

**Opción 1: Usar Python 3.11 con pyenv (Recomendado)**
```bash
# Instalar pyenv
curl https://pyenv.run | bash
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
exec $SHELL  # Recargar shell

# Instalar Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# Recrear entorno virtual
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Opción 2: Forzar instalación con Python 3.13 (si pyenv falla)**
```bash
# Limpiar entorno anterior
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Instalar por grupos para evitar conflictos
pip install --upgrade pip setuptools wheel

# Grupo 1: Básicas
pip install numpy matplotlib Pillow PyYAML requests tqdm

# Grupo 2: Hardware
pip install pyserial adafruit-blinka gpiozero

# Grupo 3: Visión (puede requerir --no-build-isolation)
pip install --no-build-isolation opencv-python-headless
pip install ultralytics picamera2
```

#### Error de conflicto de Pillow
Si ves `ERROR: Cannot install Pillow==9.4.0 and Pillow>=10.0.0`:
- El `requirements.txt` ya está corregido
- Usa la instalación por grupos de arriba

### 6. Configurar I2C y GPIO
Asegúrate de que I2C esté habilitado en Raspberry Pi:
```bash
sudo raspi-config
# Interfacing Options > I2C > Enable
```

Instalar bibliotecas necesarias:
```bash
sudo apt update
sudo apt install python3-smbus python3-dev
```

## Configuración Hardware

### Conexiones PCA9685 (Servos)
- VCC: 5V
- GND: GND
- SDA: Pin 3 (GPIO 2)
- SCL: Pin 5 (GPIO 3)
- Canales 0-3: Servos MG996R (base, hombro, codo, pinza)
- Señal de servos: VCC (5V), GND

### Conexiones TMC2208 (NEMA 17)
- VM: 12V
- GND: GND
- STEP: GPIO 17 (Pin 11)
- DIR: GPIO 18 (Pin 12)
- ENABLE: GPIO 19 (Pin 35) - Opcional
- Motor: Conectar bobinas del NEMA 17

### Cámara
- Conectar Raspberry Pi Camera al puerto CSI

## Ejecución

### Ejecutar el sistema principal
```bash
cd arm_system
python main.py
```

### Control web (Interfaz gráfica)
```bash
cd arm_system
python web_control.py
```
Luego abre tu navegador en: http://localhost:5000

**Características de la interfaz web:**
- Sliders para control preciso de cada articulación
- Botones de posiciones predefinidas
- Visualización en tiempo real de ángulos actuales
- Botones para ir a "home" y probar secuencia
- Diseño responsive para móvil y desktop

### Control manual independiente
```bash
cd arm_system
python manual_control.py
```

### Modos de operación

El sistema puede funcionar en dos modos:

#### Modo Completo (con hardware directo)
- Requiere: Raspberry Pi + PCA9685 + TMC2208 + Servos + Motor paso a paso + Cámara
- Control directo de hardware desde Raspberry Pi
- Comunicación I2C para servos, GPIO para motor paso a paso
- **Este es tu setup actual**

#### Modo Simulado/Demo (sin hardware)
- Solo requiere: Raspberry Pi con Python
- Simula detección de objetos
- Muestra movimientos sin ejecutar físicamente
- Útil para desarrollo y pruebas

### Menú de comandos
- `c`: Verificar servicios (simulado si no hay hardware)
- `s`: Servicio de seguridad (simulado si no hay hardware)
- `n`: Escanear entorno (usa simulación si no hay cámara)
- `p`: Pick & place (movimientos automáticos)
- `m`: Control manual del brazo
- `q`: Salir

#### Control Manual (comando `m`)
- `b<ángulo>`: Mover base (ej: `b90`)
- `s<ángulo>`: Mover hombro (ej: `s45`)
- `e<ángulo>`: Mover codo (ej: `e90`)
- `g<ángulo>`: Mover pinza (ej: `g0` abrir, `g90` cerrar)
- `a<mm>`: Mover brazo (ej: `a50` subir, `a-50` bajar)
- `h`: Ir a posición home (90° en todos los servos)
- `q`: Volver al menú principal

## Uso

1. Ejecuta el sistema.
2. Selecciona 'n' para escanear: captura imagen, detecta objetos con YOLO.
3. Selecciona 'p' para pick & place: elige objeto, el brazo se mueve para tomarlo y colocarlo en zona designada.
4. El sistema maneja automáticamente el control de servos y motor paso a paso.

## Notas

- Asegúrate de calibrar los servos antes de usar.
- Las zonas de colocación están predefinidas por clase de objeto.
- El sistema incluye protocolos de seguridad en caso de fallos.

## Próximos pasos

Optimización y expansión en cursos futuros.
