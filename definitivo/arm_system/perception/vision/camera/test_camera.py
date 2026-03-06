import cv2
import time
from main import CameraManager

def test_camera():
    print("Iniciando prueba de cámara...")
    
    # Crear ventana
    cv2.namedWindow("Prueba de Cámara", cv2.WINDOW_NORMAL)
    
    # Inicializar cámara
    camera = CameraManager(camera_index=0)  # Usar 0 para la primera cámara
    cap = camera.cap
    
    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara")
        return
    
    print("Cámara iniciada correctamente")
    print("Presiona 'c' para capturar una imagen")
    print("Presiona 'q' para salir")
    
    try:
        while True:
            # Leer frame
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo leer frame de la cámara")
                break
            
            # Mostrar frame
            cv2.imshow("Prueba de Cámara", frame)
            
            # Capturar tecla
            key = cv2.waitKey(1) & 0xFF
            
            # Si presiona 'q', salir
            if key == ord('q'):
                print("Cerrando prueba de cámara...")
                break
            
            # Si presiona 'c', capturar imagen
            elif key == ord('c'):
                filename = camera.capture_image()
                if filename:
                    print(f"Imagen guardada en: {filename}")
                else:
                    print("Error al capturar imagen")
    
    finally:
        # Limpieza
        cap.release()
        cv2.destroyAllWindows()
        print("Prueba de cámara finalizada")

if __name__ == "__main__":
    test_camera()