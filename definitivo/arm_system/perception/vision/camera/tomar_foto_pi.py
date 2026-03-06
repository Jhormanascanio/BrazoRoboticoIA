#!/usr/bin/env python3
from picamera2 import Picamera2
import time

print("Iniciando cámara...")
picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)

print("Iniciando preview...")
picam2.start()
time.sleep(2)  # Dar tiempo para que el sensor se ajuste

print("Capturando imagen...")
timestamp = time.strftime("%Y%m%d-%H%M%S")
filename = f"test_foto_{timestamp}.jpg"
picam2.capture_file(filename)

print(f"Foto guardada como: {filename}")
picam2.stop()
picam2.close()