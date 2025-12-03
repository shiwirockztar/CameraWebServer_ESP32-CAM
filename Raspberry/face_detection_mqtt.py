import cv2
import paho.mqtt.client as mqtt
import time, json, pickle, threading
import pytz
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- FUSEAU HORAIRE ---
CO_TZ = pytz.timezone('America/Bogota')

# --- CONFIGURATION ENVIRONNEMENT & INFLUXDB ---
load_dotenv() 

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# Initialisation InfluxDB
try:
    client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client_influx.write_api(write_options=SYNCHRONOUS)
except Exception as e:
    print(f"[ERROR] Échec de la connexion à InfluxDB : {e}")
    # Utiliser un mock pour ne pas crasher le script si la DB est inaccessible
    def write_to_influx(measurement, tags, fields):
        # print(f"[MOCK INFLUX] {measurement} logged.")
        pass
    print("[WARN] InfluxDB désactivé. Les logs seront affichés dans la console.")


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
LIMITE = 50  # cm

# Nouvelle configuration Watchdog
LED_OFF_TIMEOUT = 5.0 # Temps sans message de distance avant d'éteindre la LED
last_distancia_time = 0.0
led_last_state = False

# Détection et Reconnaissance
last_face = 0.0 
last_state = None
COOLDOWN = 2.0  # Cooldown après publication FALSE
REARM_COOLDOWN = 5.0 # Cooldown après publication TRUE

# Gestion du temporisateur
rearm_timer = None 

MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"

# ===================== MODEL LOADING =====================
try:
    if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
        raise FileNotFoundError("Model or labels are missing. Run encode_faces.py first.")

    with open(LABELS_FILE, "rb") as f:
        name_to_label = pickle.load(f)
    label_to_name = {v:k for k,v in name_to_label.items()}

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_FILE)
    print("[INFO] Modèles de reconnaissance faciale chargés.")

except FileNotFoundError as e:
    print(f"[FATAL] {e}")
    exit(1)
except Exception as e:
    print(f"[FATAL] Erreur lors du chargement des modèles : {e}")
    exit(1)

cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


# ===================== FONCTIONS D'ASSISTANCE =====================

def get_bogota_time():
    """Retourne l'heure actuelle de Bogota au format string."""
    # Correction de l'heure : Utiliser UTC comme référence pour éviter les problèmes d'horloge système
    utc_now = datetime.now(timezone.utc)
    bogota_time = utc_now.astimezone(CO_TZ)
    return bogota_time.strftime("%Y-%m-%d %H:%M:%S")

def rearm_detection():
    """Réactive la détection après le cooldown."""
    global detect_on
    detect_on = True
    print(f"[SYSTEM] Détection réactivée après {REARM_COOLDOWN}s de repos.")


# ===================== MQTT CALLBACKS & LOGIQUE DE CONTRÔLE =====================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_DISTANCIA)
        print("[MQTT] connecté, s'abonne à la distance.")
    else:
        print(f"[MQTT] Erreur de connexion, code : {rc}")

def on_message(client, userdata, msg):
    global detect_on, last_distancia_time, led_last_state, rearm_timer
    try:
        data = json.loads(msg.payload.decode())
        dist_val = data.get("distancia_cm")
        
        # 1. Mise à jour du temps de réception et log InfluxDB
        if dist_val is not None:
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": msg.topic, "direction": "incoming"},
                fields={"distancia_cm": float(dist_val)}
            )
            last_distancia_time = time.time()
            # print(f"[MQTT] Distance: {dist_val} cm") # Décommenter pour debug

        # 2. Logique d'activation de la détection faciale
        new_detect = data.get("distancia_cm", 9999) < LIMITE
        
        # Activer la détection seulement si le temporisateur de réarmement n'est PAS actif
        if rearm_timer is None or not rearm_timer.is_alive():
            detect_on = new_detect

        # 3. Logique d'activation de la LED (se produit IMMÉDIATEMENT si proche)
        if new_detect and not led_last_state:
            try:
                led_msg = {"led": True}
                client.publish(TOPIC_LED, json.dumps(led_msg))
                led_last_state = True
                print(f"[MQTT] LED ON (Distance < {LIMITE} cm).")
                write_to_influx(
                    measurement="mqtt_logs",
                    tags={"topic": TOPIC_LED, "direction": "outgoing"},
                    fields={"led_status": True}
                )
            except Exception as e:
                print(f"[MQTT] Erreur publication LED ON: {e}")
                
    except Exception as e:
        print(f"[MQTT] Erreur lors du traitement du message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# TLS
try:
    client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY)
except Exception as e:
    print(f"[WARN] Impossible de configurer TLS: {e}. Connexion sans TLS si échec.")
client.connect(BROKER, PORT, 60)
client.loop_start()

# ===================== WATCHDOG THREAD (Rétabli avec 5.0s) =====================
def distancia_watcher():
    """Vérifie si un message de distance a été reçu récemment. Si non, éteint la LED."""
    global last_distancia_time, led_last_state
    while True:
        try:
            now = time.time()
            # Si la LED est ON ET qu'aucun message n'a été reçu depuis LED_OFF_TIMEOUT
            if led_last_state and (now - last_distancia_time) > LED_OFF_TIMEOUT:
                try:
                    led_msg = {"led": False}
                    client.publish(TOPIC_LED, json.dumps(led_msg))
                    led_last_state = False
                    print(f"[WATCHER] Aucune distance reçue depuis {LED_OFF_TIMEOUT}s. LED OFF.")
                    # LOG INFLUXDB (LED OFF)
                    write_to_influx(
                        measurement="mqtt_logs",
                        tags={"topic": TOPIC_LED, "direction": "outgoing"},
                        fields={"led_status": False}
                    )
                except Exception as e:
                    print(f"[WATCHER] Erreur publication LED OFF: {e}")
        except Exception as e:
            print(f"[WATCHER] Erreur inattendue: {e}")
        time.sleep(0.5) # Vérifier toutes les 0.5 secondes

watcher_thread = threading.Thread(target=distancia_watcher, daemon=True)
watcher_thread.start()

# ===================== FACE DETECTION AND RECOGNITION =====================
def detect():
    global cap, last_face, last_state, detect_on, rearm_timer
    
    # Initialisation de la caméra
    if cap is None:
        cap = cv2.VideoCapture(URL)
        if not cap.isOpened():
            print("[ERROR] Impossible d'ouvrir le flux vidéo.")
            return
        else:
            global last_face
            last_face = time.time()
            print("[INFO] Flux vidéo ouvert. Détection initiée.")

    ret, frame = cap.read()
    if not ret:
        print("[WARN] Impossible de lire une trame du flux.")
        return
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
    now = time.time()
    face_detected = False
    THRESH = 95.0 

    for (x,y,w,h) in detected:
        if w < 30 or h < 30: continue

        face_roi = gray[y:y+h, x:x+w]
        if face_roi.size == 0: continue
        face_resized = cv2.resize(face_roi, (200,200))

        # Prédiction
        label, confidence = recognizer.predict(face_resized)
        name = "Unknown"
        
        # Logique de reconnaissance
        if confidence < THRESH and label in label_to_name:
            name = label_to_name[label]
            face_detected = True
            
            # --- LOGIQUE D'AUTORISATION TRUE ---
            if last_state != True:
                msg = {
                    "camera": "camera1",
                    "authorization": True,
                    "time": get_bogota_time(), # Heure de Bogota corrigée
                    "name": name,
                    "confidence": float(confidence)
                }
                client.publish(TOPIC_ROSTRO, json.dumps(msg))
                write_to_influx(
                    measurement="mqtt_logs",
                    tags={"topic": TOPIC_ROSTRO, "direction": "outgoing"},
                    fields={"authorization": 1, "name": name, "confidence": float(confidence)}
                )
                print(f"[MQTT] Autorisation TRUE ({name}, C:{int(confidence)}) publiée. Repos de {REARM_COOLDOWN}s.")
                last_state = True
                
                # Activation du cooldown de réarmement
                detect_on = False
                rearm_timer = threading.Timer(REARM_COOLDOWN, rearm_detection)
                rearm_timer.start()

                break 
        
    # Publication FALSE après cooldown s'il n'y a pas eu de détection valide
    if not face_detected and (now - last_face > COOLDOWN) and last_state != False and detect_on:
        msg = {"authorization": False, "time": get_bogota_time()} # Heure de Bogota
        client.publish(TOPIC_ROSTRO, json.dumps(msg))
        write_to_influx(
            measurement="mqtt_logs",
            tags={"topic": TOPIC_ROSTRO, "direction": "outgoing"},
            fields={"authorization": 0}
        )
        print("[MQTT] Autorisation FALSE publiée.")
        last_state = False

    if face_detected:
        last_face = now

# ===================== BOUCLE D'EXÉCUTION PRINCIPALE =====================
if __name__ == "__main__":
    print("[SYSTEM] Démarrage du système de détection faciale.")
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
        print("\n[SYSTEM] Arrêt du script.")