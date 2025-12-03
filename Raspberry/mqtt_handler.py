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
rearm_timer = None # Le temporisateur de réarmement (géré par main_loop, mais réinitialisé ici)

# ===================== FONCTIONS D'ASSISTANCE =====================

def set_detection_state(state: bool):
    """Mise à jour de l'état d'activation de la détection."""
    global detect_on
    detect_on = state

def set_rearm_timer(timer):
    """Mise à jour du temporisateur de réarmement."""
    global rearm_timer
    rearm_timer = timer
    
def get_rearm_timer():
    """Retourne l'état du temporisateur de réarmement."""
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
            print("[WATCHER] LED OFF (Watchdog/Distance dépassée).")
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
            # Si la LED est ON ET qu'aucun message n'a été reçu depuis LED_OFF_TIMEOUT
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
        data = json.loads(msg.payload.decode())
        dist_val = data.get("distancia_cm")
        
        if dist_val is not None:
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": msg.topic, "direction": "incoming"},
                fields={"distancia_cm": float(dist_val)}
            )
            last_distancia_time = time.time()

        is_close = data.get("distancia_cm", 9999) < LIMITE_DISTANCE
        
        # 1. Activation de la détection (si le cooldown n'est pas actif)
        current_rearm_timer = get_rearm_timer()
        if current_rearm_timer is None or not current_rearm_timer.is_alive():
            set_detection_state(is_close)

        # 2. Logique d'activation de la LED (se produit IMMÉDIATEMENT si proche)
        if is_close and not led_last_state:
            try:
                led_msg = {"led": True}
                client.publish(TOPIC_LED, json.dumps(led_msg))
                led_last_state = True
                print(f"[MQTT] LED ON (Distance < {LIMITE_DISTANCE} cm).")
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
    # Le script peut continuer, mais la détection sera désactivée si non forcée dans main_loop.py

# Démarrer le Watchdog
watcher_thread = threading.Thread(target=distancia_watcher, daemon=True)
watcher_thread.start()

# Fonctions exposées
def is_detection_enabled():
    return detect_on

def publish_face_auth(msg):
    """Publie un message d'autorisation (TRUE/FALSE) sur le topic ROSTRO."""
    mqtt_client.publish(TOPIC_ROSTRO, json.dumps(msg))

def stop_mqtt():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()