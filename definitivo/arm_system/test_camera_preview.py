#!/usr/bin/env python3
"""
Script de prueba para ver la cámara en tiempo real
"""
import cv2
import numpy as np
from picamera2 import Picamera2
import time

def test_camera():
    print("Inicializando cámara...")
    picam = Picamera2()
    
    # Configuración para preview
    config = picam.create_preview_configuration(
        main={"size": (640, 480)}
    )
    picam.configure(config)
    picam.start()
    
    print("Esperando 2 segundos para que la cámara se ajuste...")
    time.sleep(2)
    
    print("\nPresiona 'q' para salir, 's' para capturar imagen")
    print("Mostrando preview de cámara...\n")
    
    try:
        while True:
            # Capturar frame
            image = picam.capture_array()
            
            # Rotar 180 grados
            image = np.rot90(image, 2)
            
            # Convertir RGB a BGR para OpenCV
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Mostrar
            cv2.imshow('Camera Preview - Press Q to quit, S to save', image_bgr)
            
            # Esperar tecla
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("Saliendo...")
                break
            elif key == ord('s'):
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"test_capture_{timestamp}.jpg"
                cv2.imwrite(filename, image_bgr)
                print(f"Imagen guardada: {filename}")
    
    except KeyboardInterrupt:
        print("\nInterrumpido por usuario")
    
    finally:
        cv2.destroyAllWindows()
        picam.stop()
        picam.close()
        print("Cámara cerrada")

if __name__ == '__main__':
    test_camera()
