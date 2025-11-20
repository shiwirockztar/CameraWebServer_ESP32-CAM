# face_detection_mqtt.py
import cv2
import paho.mqtt.client as mqtt
import time, json, pickle
from datetime import datetime
import os

# ===================== CONFIG MQTT =====================
BROKER = "totox.local"
PORT = 8883
TOPIC_ROSTRO = "sensor/rostro"
TOPIC_DISTANCIA = "sensor/distancia"
CA = "ca.crt"
CERT = "server.crt"
KEY = "server.key"

# ===================== VARIABLES =====================
URL = "http://192.168.61.202:81/stream"  # adapte
cap = None
detect_on = False
LIMITE = 50  # cm

ultimo_rostro = 0
ultimo_estado = None
COOLDOWN = 2.0  # secondes

MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"

# ===================== CHARGEMENT DU MODELE =====================
if not os.path.exists(MODEL_FILE) or not os.path.exists(LABELS_FILE):
    raise FileNotFoundError("Modèle ou labels manquent. Lance encode_faces.py d'abord.")

# load label map (nom -> int), on inverse pour int->nom
with open(LABELS_FILE, "rb") as f:
    name_to_label = pickle.load(f)
label_to_name = {v:k for k,v in name_to_label.items()}

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_FILE)

# Chargement du cascade pour detection
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ===================== MQTT =====================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_DISTANCIA)
        print("[MQTT] connecté, subscribe distance")
    else:
        print("[MQTT] rc:", rc)

def on_message(client, userdata, msg):
    global detect_on
    try:
        data = json.loads(msg.payload.decode())
        detect_on = data.get("distancia_cm", 9999) < LIMITE
    except Exception as e:
        print("[MQTT] erreur message:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# TLS si besoin
try:
    client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY)
except Exception as e:
    print("[WARN] impossible de configurer TLS:", e)
client.connect(BROKER, PORT, 60)
client.loop_start()

# ===================== DÉTECTION ET RECONNAISSANCE =====================
def detectar():
    global cap, ultimo_rostro, ultimo_estado
    if cap is None:
        cap = cv2.VideoCapture(URL)
        if not cap.isOpened():
            print("[ERROR] Impossible d'ouvrir le flux vidéo")
            return

    ret, frame = cap.read()
    if not ret:
        return

    # rotation si nécessaire
    try:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    except Exception:
        pass

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
    now = time.time()
    rostro_detectado = False

    for (x,y,w,h) in detected:
        # ignore very small faces
        if w < 30 or h < 30:
            continue

        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200,200))

        # predict
        label, confidence = recognizer.predict(face_resized)
        # LBPH: lower confidence = better match. Ajuste le seuil selon tests (ex: 50..80)
        THRESH = 110.0
        name = "Unknown"
        if confidence <= THRESH and label in label_to_name:
            name = label_to_name[label]
            rostro_detectado = True
            if ultimo_estado != True:
                msg = {
                    "autorizacion": True,
                    "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "nombre": name,
                    "confidence": float(confidence)
                }
                client.publish(TOPIC_ROSTRO, json.dumps(msg))
                ultimo_estado = True
        # dessiner
        try:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0) if name!="Unknown" else (0,0,255), 2)
            cv2.putText(frame, f"{name} ({int(confidence)})", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0) if name!="Unknown" else (0,0,255), 2)
        except Exception:
            pass

    # no face recognized -> publish False after cooldown
    if not rostro_detectado and (now - ultimo_rostro > COOLDOWN) and ultimo_estado != False:
        msg = {"autorizacion": False, "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        client.publish(TOPIC_ROSTRO, json.dumps(msg))
        ultimo_estado = False

    if rostro_detectado:
        ultimo_rostro = now

    # affichage (s'il y a un backend Qt manquant, on ignore l'erreur et on continue en headless)
    try:
        cv2.imshow("Cam", frame)
    except cv2.error as e:
        # pas de GUI dispo (Wayland/Qt) -> on ignore
        pass

# ===================== LOOP =====================
try:
    while True:
        if detect_on:
            detectar()
        else:
            time.sleep(0.5)
        # gestion clavier si GUI ok
        try:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception:
            # pas de GUI -> on continue
            pass
except KeyboardInterrupt:
    pass
finally:
    if cap:
        cap.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass
    client.loop_stop()
    client.disconnect()
