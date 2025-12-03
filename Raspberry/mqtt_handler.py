# mqtt_handler.py

import paho.mqtt.client as mqtt
import time, json, threading
from config import (
    BROKER, PORT, TOPIC_DISTANCIA, TOPIC_LED, LIMITE_DISTANCE, 
    LED_OFF_TIMEOUT, CA_FILE, CERT_FILE, KEY_FILE, TOPIC_ROSTRO
)
from influx_handler import write_to_influx

# Variables globales pour le contrôle
last_distancia_time = 0.0
led_last_state = False
detect_on = False
rearm_timer = None 

# ===================== FONCTIONS D'ASSISTANCE =====================

def set_detection_state(state: bool):
    global detect_on
    detect_on = state

def set_rearm_timer(timer):
    global rearm_timer
    rearm_timer = timer
    
def get_rearm_timer():
    global rearm_timer
    return rearm_timer

# ===================== LOGIQUE LED / WATCHDOG =====================

def turn_off_led():
    """Éteint la LED et publie l'état via MQTT et InfluxDB."""
    global led_last_state
    if led_last_state:
        try:
            led_msg = {"led": False}
            mqtt_client.publish(TOPIC_LED, json.dumps(led_msg))
            led_last_state = False
            # --- AFFICHAGE DEBOGAGE ENVOI ---
            print(f"[MQTT ENVOI] -> {TOPIC_LED}: {json.dumps(led_msg)} (LED OFF)")
            # ---------------------------------
            
            # LOG INFLUXDB
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": TOPIC_LED, "direction": "outgoing"},
                fields={"led_status": False}
            )
        except Exception as e:
            print(f"[WATCHER] Erreur publication LED OFF: {e}")

def distancia_watcher():
    """Thread Watchdog : Éteint la LED si aucun message n'est reçu depuis LED_OFF_TIMEOUT."""
    global last_distancia_time
    while True:
        try:
            now = time.time()
            if led_last_state and (now - last_distancia_time) > LED_OFF_TIMEOUT:
                turn_off_led()
        except Exception as e:
            print(f"[WATCHER] Erreur inattendue: {e}")
        time.sleep(0.5)

# ===================== MQTT CALLBACKS =====================

def on_connect(client, userdata, flags, rc):
    """Gère la connexion MQTT."""
    if rc == 0:
        client.subscribe(TOPIC_DISTANCIA)
        print("[MQTT] Connecté et abonné à la distance.")
    else:
        print(f"[MQTT] Échec de connexion: {rc}")

def on_message(client, userdata, msg):
    """Gère les messages entrants de distance."""
    global last_distancia_time, led_last_state
    try:
        payload_str = msg.payload.decode()
        data = json.loads(payload_str)
        dist_val = data.get("distancia_cm")
        
        # --- AFFICHAGE DEBOGAGE RÉCEPTION (AJOUTÉ/MODIFIÉ) ---
        print(f"[MQTT REÇU] <- {msg.topic}: {payload_str}")
        # -----------------------------------------------------
        
        # 1. Mise à jour du temps de réception et log InfluxDB
        if dist_val is not None:
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": msg.topic, "direction": "incoming"},
                fields={"distancia_cm": float(dist_val)}
            )
            last_distancia_time = time.time()

        # 2. Logique d'activation de la détection faciale
        is_close = data.get("distancia_cm", 9999) < LIMITE_DISTANCE
        
        current_rearm_timer = get_rearm_timer()
        if current_rearm_timer is None or not current_rearm_timer.is_alive():
            set_detection_state(is_close)

        # 3. Logique d'activation de la LED
        if is_close and not led_last_state:
            try:
                led_msg = {"led": True}
                client.publish(TOPIC_LED, json.dumps(led_msg))
                led_last_state = True
                
                # --- AFFICHAGE DEBOGAGE ENVOI ---
                print(f"[MQTT ENVOI] -> {TOPIC_LED}: {json.dumps(led_msg)} (LED ON)")
                # ---------------------------------
                
                write_to_influx(
                    measurement="mqtt_logs",
                    tags={"topic": TOPIC_LED, "direction": "outgoing"},
                    fields={"led_status": True}
                )
            except Exception as e:
                print(f"[MQTT] Erreur publication LED ON: {e}")
                
    except Exception as e:
        print(f"[MQTT] Erreur lors du traitement du message: {e}")

# ===================== INITIALISATION MQTT =====================

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# TLS
try:
    mqtt_client.tls_set(ca_certs=CA_FILE, certfile=CERT_FILE, keyfile=KEY_FILE)
    print("[MQTT] Configuration TLS appliquée.")
except Exception as e:
    print(f"[WARN] Impossible de configurer TLS: {e}. Tentative de connexion sans TLS.")

try:
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[FATAL] Échec de la connexion MQTT: {e}")

# Démarrer le Watchdog
watcher_thread = threading.Thread(target=distancia_watcher, daemon=True)
watcher_thread.start()