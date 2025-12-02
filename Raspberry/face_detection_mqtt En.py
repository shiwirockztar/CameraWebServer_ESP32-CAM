# face_detection_production_headless_cooldown_v3.py
import cv2
import paho.mqtt.client as mqtt
import time, json, pickle, threading
from datetime import datetime
import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CONFIGURATION INFLUXDB ---
load_dotenv() 

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_influx.write_api(write_options=SYNCHRONOUS)

# ===================== CONFIG MQTT =====================
BROKER = "totox.local"
PORT = 8883
TOPIC_ROSTRO = "sensor/rostro"
TOPIC_DISTANCIA = "sensor/distancia"
TOPIC_LED = "actuator/led"
CA = "ca.crt"
CERT = "server.crt"
KEY = "server.key"

# ===================== VARIABLES GLOBALES =====================
URL = "http://10.42.0.202:81/stream"
cap = None
detect_on = False
LIMITE = 7  # cm

# Distance topic watchdog: track last received time and LED state
last_distancia_time = 0.0
led_last_state = False
DIST_TIMEOUT = 3.0  # seconds without messages -> LED off

# Variables de détection
last_face = 0.0 
last_state = None
COOLDOWN = 2.0  # seconds (cooldown après FALSE)
REARM_COOLDOWN = 5.0 # NOUVEAU: Cooldown après détection TRUE

# État du temporisateur de réactivation
rearm_timer = None 

MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"

# --- FONCTION INFLUXDB ---
def write_to_influx(measurement, tags, fields):
    try:
        p = Point(measurement)
        for key, value in tags.items():
            p.tag(key, value)
        for key, value in fields.items():
            p.field(key, value)
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
    except Exception as e:
        print(f"[INFLUX] Error writing: {e}")

# ===================== MODEL LOADING =====================
if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
    raise FileNotFoundError("Model or labels are missing. Run encode_faces.py first.")

with open(LABELS_FILE, "rb") as f:
    name_to_label = pickle.load(f)
label_to_name = {v:k for k,v in name_to_label.items()}

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_FILE)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


# ===================== FONCTION DE RÉARMEMENT =====================
def rearm_detection():
    """Réactive la détection après le cooldown de 5 secondes."""
    global detect_on
    detect_on = True
    print(f"[SYSTEM] Détection réactivée après {REARM_COOLDOWN}s de repos.")


# ===================== MQTT CALLBACKS & WATCHDOG =====================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_DISTANCIA)
        print("[MQTT] connected, subscribe to distance")
    else:
        print("[MQTT] rc:", rc)

def on_message(client, userdata, msg):
    global detect_on, last_distancia_time, led_last_state, rearm_timer
    try:
        data = json.loads(msg.payload.decode())
        print("[MQTT] distancia payload:", data)
        dist_val = data.get("distancia_cm")
        
        # LOG INFLUXDB (Distance)
        if dist_val is not None:
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": msg.topic, "direction": "incoming"},
                fields={"distancia_cm": float(dist_val)}
            )
            
        new_detect = data.get("distancia_cm", 9999) < LIMITE
        
        # ACTIVER LA DETECTION SEULEMENT SI LE TEMPORISATEUR N'EST PAS ACTIF
        if rearm_timer is None or not rearm_timer.is_alive():
            detect_on = new_detect

        last_distancia_time = time.time()

        # Publication LED ON
        if not led_last_state:
            try:
                led_msg = {"led": True}
                client.publish(TOPIC_LED, json.dumps(led_msg))
                led_last_state = True
                print(f"[MQTT] LED -> {led_msg} on {TOPIC_LED}")
                # LOG INFLUXDB (LED ON)
                write_to_influx(
                    measurement="mqtt_logs",
                    tags={"topic": TOPIC_LED, "direction": "outgoing"},
                    fields={"led_status": True}
                )
            except Exception as e:
                print("[MQTT] error publishing LED ON:", e)
    except Exception as e:
        print("[MQTT] error with message:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# TLS if needed
try:
    client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY)
except Exception as e:
    print("[WARN] unable to configure TLS:", e)
client.connect(BROKER, PORT, 60)
client.loop_start()

# Watchdog Thread (inchangé)
def distancia_watcher():
    global last_distancia_time, led_last_state
    while True:
        try:
            now = time.time()
            if led_last_state and (now - last_distancia_time) > DIST_TIMEOUT:
                try:
                    led_msg = {"led": False}
                    client.publish(TOPIC_LED, json.dumps(led_msg))
                    led_last_state = False
                    print(f"[WATCHER] No distancia msg for {DIST_TIMEOUT}s, published {led_msg} on {TOPIC_LED}")
                    # LOG INFLUXDB (LED OFF)
                    write_to_influx(
                        measurement="mqtt_logs",
                        tags={"topic": TOPIC_LED, "direction": "outgoing"},
                        fields={"led_status": False}
                    )
                except Exception as e:
                    print("[WATCHER] error publishing LED OFF:", e)
        except Exception as e:
            print("[WATCHER] unexpected error:", e)
        time.sleep(0.2)

watcher_thread = threading.Thread(target=distancia_watcher, daemon=True)
watcher_thread.start()

# ===================== FACE DETECTION AND RECOGNITION =====================
def detect():
    global cap, last_face, last_state, detect_on, rearm_timer
    
    # Initialisation de la caméra (CORRIGÉE : initialisation du chronomètre)
    if cap is None:
        cap = cv2.VideoCapture(URL)
        if not cap.isOpened():
            print("[ERROR] Unable to open the video stream")
            return
        else:
            global last_face
            last_face = time.time() # Initialise le chronomètre ici
            print("[INFO] Stream opened and detection loop initiated.")

    ret, frame = cap.read()
    if not ret:
        return
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
    now = time.time()
    face_detected = False

    for (x,y,w,h) in detected:
        if w < 30 or h < 30: continue

        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0: continue
        face_resized = cv2.resize(face_roi, (200,200))

        # predict
        label, confidence = recognizer.predict(face_resized)
        
        # **** NOUVEAU SEUIL DE DÉCLENCHEMENT/AFFICHAGE ****
        THRESH = 95.0 
        
        name = "Unknown"
        
        # La condition est maintenant: La confiance doit être < 95.0
        if confidence < THRESH and label in label_to_name:
            name = label_to_name[label]
            face_detected = True
            
            # DEBUG : Impression directe dans la console pour la détection valide
            print(f"[DEBUG] Visage détecté : {name} | Confiance: {int(confidence)} (SOUS LE SEUIL DE {THRESH})")

            # --- LOGIQUE D'AUTORISATION ET DE REPOS ---
            if last_state != True:
                msg = {
                    "authorization": True,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "confidence": float(confidence)
                }
                client.publish(TOPIC_ROSTRO, json.dumps(msg))
                print(f"[MQTT] Autorisation TRUE publiée pour {name}. Démarrage du repos de {REARM_COOLDOWN}s.")
                last_state = True
                
                # 1. DÉSACVITER LA DÉTECTION IMMÉDIATEMENT
                detect_on = False
                
                # 2. DÉMARRER LE TEMPORISATEUR DE RÉACTIVATION
                rearm_timer = threading.Timer(REARM_COOLDOWN, rearm_detection)
                rearm_timer.start()

                break 
        
        # NOUVEAU: Si le visage est détecté mais que la confiance est >= 95.0, on ne fait rien (pas de print, pas de MQTT).
        # Le script continue de boucler.

    # no face recognized -> publish False after cooldown (si pas en repos)
    # Note: La publication FALSE est basée sur l'absence de DÉTECTION VALIDE (<95.0)
    if not face_detected and (now - last_face > COOLDOWN) and last_state != False and detect_on:
        msg = {"authorization": False, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        client.publish(TOPIC_ROSTRO, json.dumps(msg))
        print("[MQTT] Autorisation FALSE publiée.")
        last_state = False

    if face_detected:
        last_face = now

# ===================== LOOP D'EXÉCUTION =====================
if __name__ == "__main__":
    try:
        while True:
            if detect_on:
                detect()
            else:
                time.sleep(0.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        if cap:
            cap.release()
        client.loop_stop()
        client.disconnect()
        print("\nArrêt du script.")