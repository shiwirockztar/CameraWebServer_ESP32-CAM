# main_loop.py

import cv2
import time, threading
from datetime import datetime, timezone
import pytz

# Importations des modules locaux
import mqtt_handler as mh
from face_recognizer import process_frame
from influx_handler import write_to_influx
from config import URL_CAMERA, CO_TZ, REARM_COOLDOWN, COOLDOWN_FALSE, TOPIC_ROSTRO

# ===================== VARIABLES GLOBALES =====================
cap = None
last_face = 0.0 
last_state = None # Dernier état d'autorisation publié (True/False)

# ===================== FONCTIONS D'ASSISTANCE =====================

def get_bogota_time():
    """Retourne l'heure actuelle de Bogota au format string."""
    # Utilise UTC comme référence pour éviter les problèmes d'horloge système mal configurée
    utc_now = datetime.now(timezone.utc)
    bogota_time = utc_now.astimezone(CO_TZ)
    return bogota_time.strftime("%Y-%m-%d %H:%M:%S")

def rearm_detection_callback():
    """Rappel pour réactiver la détection après le cooldown."""
    mh.set_detection_state(True)
    print(f"[SYSTEM] Détection réactivée après {REARM_COOLDOWN}s de repos.")
    mh.set_rearm_timer(None) # Nettoyer la référence du timer

# ===================== BOUCLE DE DÉTECTION =====================

def detect_loop():
    global cap, last_face, last_state
    
    # 1. Initialisation de la caméra
    if cap is None:
        cap = cv2.VideoCapture(URL_CAMERA)
        if not cap.isOpened():
            print("[ERROR] Impossible d'ouvrir le flux vidéo.")
            return
        else:
            last_face = time.time()
            print("[INFO] Flux vidéo ouvert. Détection initiée.")

    ret, frame = cap.read()
    if not ret:
        print("[WARN] Impossible de lire une trame du flux.")
        return
    
    # 2. Traitement de la trame pour la reconnaissance
    valid_detections = process_frame(frame)
    now = time.time()
    face_detected_valid = len(valid_detections) > 0

    if face_detected_valid:
        last_face = now
        detection = valid_detections[0] # On prend la première détection
        name = detection["name"]
        confidence = detection["confidence"]
        
        # --- LOGIQUE D'AUTORISATION TRUE ---
        if last_state != True:
            msg = {
                "camera": "camera1",
                "authorization": True,
                "time": get_bogota_time(),
                "name": name,
                "confidence": confidence
            }
            mh.publish_face_auth(msg)
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": TOPIC_ROSTRO, "direction": "outgoing"},
                fields={"authorization": 1, "name": name, "confidence": confidence}
            )
            print(f"[MQTT] Autorisation TRUE ({name}, C:{int(confidence)}) publiée. Repos de {REARM_COOLDOWN}s.")
            last_state = True
            
            # Activation du cooldown de réarmement
            mh.set_detection_state(False)
            rearm_timer = threading.Timer(REARM_COOLDOWN, rearm_detection_callback)
            rearm_timer.start()
            mh.set_rearm_timer(rearm_timer) # Stocker le timer dans mqtt_handler pour l'accès
            

    # 3. Publication FALSE après cooldown s'il n'y a pas eu de détection valide
    if not face_detected_valid and (now - last_face > COOLDOWN_FALSE) and last_state != False and mh.is_detection_enabled():
        msg = {"authorization": False, "time": get_bogota_time()}
        mh.publish_face_auth(msg)
        write_to_influx(
            measurement="mqtt_logs",
            tags={"topic": TOPIC_ROSTRO, "direction": "outgoing"},
            fields={"authorization": 0}
        )
        print("[MQTT] Autorisation FALSE publiée.")
        last_state = False

# ===================== POINT D'ENTRÉE PRINCIPAL =====================
if __name__ == "__main__":
    print("--- Démarrage du système de surveillance ---")
    
    # S'assurer que le système démarre avec la détection désactivée (en attente du signal distance)
    mh.set_detection_state(False) 

    try:
        while True:
            # La détection n'a lieu que si mqtt_handler l'a activée (via la distance)
            if mh.is_detection_enabled():
                detect_loop()
            else:
                # La détection est en cooldown (après TRUE) ou en attente de la distance
                time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        if cap:
            cap.release()
        mh.stop_mqtt()
        print("\n[SYSTEM] Arrêt du script.")