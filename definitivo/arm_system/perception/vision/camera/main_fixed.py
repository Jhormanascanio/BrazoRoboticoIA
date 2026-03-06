import os
import time
import numpy as np
import subprocess
import cv2

class CameraManager:
    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, flip: bool = True):
        self.flip = flip
        self.width = width
        self.height = height
        
        # Intentar detectar si rpicam-still está disponible (Raspberry Pi)
        try:
            result = subprocess.run(['which', 'rpicam-still'], 
                                  capture_output=True, text=True, timeout=2)
            self.use_rpicam = result.returncode == 0
        except:
            self.use_rpicam = False
        
        if self.use_rpicam:
            print("INFO: Usando rpicam-still para captura")
        else:
            print("INFO: Usando OpenCV para captura")
            self.cap = cv2.VideoCapture(camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    def _flip_image(self, image):
        """Invertir imagen 180 grados"""
        if self.flip:
            return cv2.rotate(image, cv2.ROTATE_180)
        return image
        
    def capture_image(self, save: bool = True):
        """Capturar imagen y opcionalmente guardarla"""
        try:
            if self.use_rpicam:
                # Capturar con rpicam-still (más confiable)
                temp_file = "/tmp/capture_temp.jpg"
                
                cmd = [
                    'rpicam-still',
                    '-o', temp_file,
                    '--width', str(self.width),
                    '--height', str(self.height),
                    '-t', '1',  # Timeout de 1ms (inmediato)
                    '-n'  # No preview
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                
                if result.returncode != 0:
                    print(f"ERROR: rpicam-still falló: {result.stderr.decode()}")
                    return None, None
                
                # Leer la imagen capturada
                image = cv2.imread(temp_file)
                
                if image is None:
                    print(f"ERROR: No se pudo leer {temp_file}")
                    return None, None
                
                # Limpiar archivo temporal
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
            else:
                # Capturar con OpenCV
                for _ in range(5):
                    self.cap.grab()
                
                ret, image = self.cap.read()
                if not ret:
                    print("ERROR: OpenCV no pudo capturar imagen")
                    return None, None
            
            # Invertir imagen si está habilitado
            image = self._flip_image(image)
            
            if save:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{current_dir}/objects_images/{timestamp}.jpg"
                
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                cv2.imwrite(filename, image)
                
                return image, filename
            
            return image, None
            
        except Exception as e:
            print(f"ERROR en capture_image: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None, None
        
    def __del__(self):
        if not self.use_rpicam and hasattr(self, 'cap'):
            self.cap.release()
