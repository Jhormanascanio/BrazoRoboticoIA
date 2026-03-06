"""
Detector de colores HSV para clasificar objetos y localizar recipientes.
Trabaja en conjunto con YOLO: YOLO detecta el objeto, este modulo analiza
su color dominante para decidir en que recipiente depositarlo.
"""
import cv2
import numpy as np
import logging as log

RANGOS_COLOR_HSV = {
    'rojo': [
        {'h_min': 0, 'h_max': 10, 's_min': 70, 's_max': 255, 'v_min': 50, 'v_max': 255},
        {'h_min': 170, 'h_max': 180, 's_min': 70, 's_max': 255, 'v_min': 50, 'v_max': 255},
    ],
    'azul': [
        {'h_min': 100, 'h_max': 130, 's_min': 50, 's_max': 255, 'v_min': 50, 'v_max': 255},
    ],
    'verde': [
        {'h_min': 35, 'h_max': 85, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255},
    ],
    'amarillo': [
        {'h_min': 18, 'h_max': 35, 's_min': 50, 's_max': 255, 'v_min': 80, 'v_max': 255},
    ],
    'naranja': [
        {'h_min': 10, 'h_max': 22, 's_min': 100, 's_max': 255, 'v_min': 80, 'v_max': 255},
    ],
    'morado': [
        {'h_min': 125, 'h_max': 155, 's_min': 40, 's_max': 255, 'v_min': 40, 'v_max': 255},
    ],
}


class DetectorColor:
    """Analiza regiones de imagen para determinar color dominante."""

    def __init__(self, rangos_personalizados=None):
        self.rangos = rangos_personalizados or RANGOS_COLOR_HSV

    def color_dominante_region(self, imagen_bgr, bbox):
        """Dado un bounding box (x1,y1,x2,y2) en una imagen BGR,
        retorna el nombre del color dominante y su porcentaje de cobertura."""
        x1, y1, x2, y2 = map(int, bbox)
        h, w = imagen_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 - x1 < 5 or y2 - y1 < 5:
            return 'desconocido', 0.0

        recorte = imagen_bgr[y1:y2, x1:x2]
        hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
        total_pixeles = hsv.shape[0] * hsv.shape[1]

        mejor_color = 'desconocido'
        mejor_pct = 0.0

        for nombre_color, rangos_lista in self.rangos.items():
            mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for rango in rangos_lista:
                inferior = np.array([rango['h_min'], rango['s_min'], rango['v_min']])
                superior = np.array([rango['h_max'], rango['s_max'], rango['v_max']])
                mascara_total = cv2.bitwise_or(mascara_total, cv2.inRange(hsv, inferior, superior))

            pixeles_color = cv2.countNonZero(mascara_total)
            porcentaje = pixeles_color / total_pixeles

            if porcentaje > mejor_pct:
                mejor_pct = porcentaje
                mejor_color = nombre_color

        if mejor_pct < 0.08:
            return 'desconocido', mejor_pct

        return mejor_color, mejor_pct

    def detectar_recipientes(self, imagen_bgr, area_minima=2000):
        """Busca rectangulos grandes de colores solidos (recipientes) en la imagen.
        Retorna lista de dict con: color, bbox, centro, area."""
        hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
        recipientes = []

        for nombre_color, rangos_lista in self.rangos.items():
            mascara_total = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for rango in rangos_lista:
                inferior = np.array([rango['h_min'], rango['s_min'], rango['v_min']])
                superior = np.array([rango['h_max'], rango['s_max'], rango['v_max']])
                mascara_total = cv2.bitwise_or(mascara_total, cv2.inRange(hsv, inferior, superior))

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            mascara_total = cv2.morphologyEx(mascara_total, cv2.MORPH_CLOSE, kernel)
            mascara_total = cv2.morphologyEx(mascara_total, cv2.MORPH_OPEN, kernel)

            contornos, _ = cv2.findContours(mascara_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contorno in contornos:
                area = cv2.contourArea(contorno)
                if area < area_minima:
                    continue

                x, y, w, h = cv2.boundingRect(contorno)
                aspecto = w / h if h > 0 else 0
                if 0.3 < aspecto < 3.5:
                    centro = (x + w // 2, y + h // 2)
                    recipientes.append({
                        'color': nombre_color,
                        'bbox': (x, y, x + w, y + h),
                        'centro': centro,
                        'area': area,
                    })

        recipientes.sort(key=lambda r: r['area'], reverse=True)
        return recipientes

    def posicion_relativa_en_imagen(self, centro, ancho_imagen):
        """Convierte posicion X del centro de un objeto en la imagen
        a una estimacion de pasos del stepper para la base.
        Retorna un valor de -1.0 (extremo izquierdo) a 1.0 (extremo derecho)."""
        cx = centro[0]
        return (cx / ancho_imagen - 0.5) * 2.0

    def dibujar_resultados(self, imagen, objetos_detectados, recipientes):
        """Dibuja bboxes de objetos y recipientes sobre la imagen."""
        colores_bgr = {
            'rojo': (0, 0, 255), 'azul': (255, 0, 0), 'verde': (0, 255, 0),
            'amarillo': (0, 255, 255), 'naranja': (0, 140, 255),
            'morado': (180, 0, 255), 'desconocido': (128, 128, 128),
        }
        vis = imagen.copy()

        for obj in objetos_detectados:
            x1, y1, x2, y2 = map(int, obj['bbox'])
            color_bgr = colores_bgr.get(obj.get('color', ''), (255, 255, 255))
            cv2.rectangle(vis, (x1, y1), (x2, y2), color_bgr, 2)
            etiqueta = f"{obj.get('clase', '?')} [{obj.get('color', '?')}] {obj.get('confianza', 0):.0%}"
            cv2.putText(vis, etiqueta, (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

        for rec in recipientes:
            x1, y1, x2, y2 = rec['bbox']
            color_bgr = colores_bgr.get(rec['color'], (200, 200, 200))
            cv2.rectangle(vis, (x1, y1), (x2, y2), color_bgr, 3)
            cv2.putText(vis, f"REC:{rec['color']}", (x1, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)

        return vis
