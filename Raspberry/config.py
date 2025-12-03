# config.py

import os
import pytz
from dotenv import load_dotenv

# Charger les variables d'environnement (pour InfluxDB)
load_dotenv() 

# --- FUSEAU HORAIRE ---
# Bogota (UTC-5) pour l'horodatage
CO_TZ = pytz.timezone('America/Bogota')

# --- CONFIGURATION MQTT ---
BROKER = "totox.local"
PORT = 8883
TOPIC_ROSTRO = "sensor/rostro" # Sortie: Autorisation TRUE/FALSE
TOPIC_DISTANCIA = "sensor/distancia" # Entrée: Messages de distance
TOPIC_LED = "actuator/led" # Sortie: Contrôle de la LED

# --- CONFIGURATION INFLUXDB ---
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# --- VARIABLES DU SYSTÈME ---
URL_CAMERA = "http://10.42.0.202:81/stream"

# Seuil de distance pour activer la détection (en cm)
LIMITE_DISTANCE = 50  

# Temps sans message de distance avant d'éteindre la LED (Watchdog)
LED_OFF_TIMEOUT = 5.0 

# Cooldown après une détection valide TRUE (temps de repos)
REARM_COOLDOWN = 5.0 

# Cooldown après une détection FALSE (pour éviter le spam FALSE)
COOLDOWN_FALSE = 2.0  

# Seuil de confiance pour la reconnaissance faciale (inférieur à ce chiffre est une bonne reconnaissance)
RECOGNITION_THRESHOLD = 80.0

# --- FICHIERS MODÈLES ---
MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"
CA_FILE = "ca.crt"
CERT_FILE = "server.crt"
KEY_FILE = "server.key"