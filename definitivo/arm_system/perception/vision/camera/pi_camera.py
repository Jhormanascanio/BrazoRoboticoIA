import os
import time
from picamera2 import Picamera2

class PiCameraManager:
    def __init__(self):
        self.camera = Picamera2()
        config = self.camera.create_still_configuration()
        self.camera.configure(config)
        self.camera.start()
        # Dar tiempo para que el sensor se ajuste
        time.sleep(2)
        
    def capture_image(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{current_dir}/objects_images/{timestamp}.jpg"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        self.camera.capture_file(filename)
        return filename
        
    def __del__(self):
        self.camera.stop()
        self.camera.close()