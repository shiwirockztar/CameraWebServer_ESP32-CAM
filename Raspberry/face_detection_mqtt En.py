# face_detection_mqtt.py
import cv2
import paho.mqtt.client as mqtt
import time, json, pickle
from dotenv import load_dotenv
from datetime import datetime
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os

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

# ===================== VARIABLES =====================
URL = "http://10.42.0.202:81/stream"  # adapte
cap = None
detect_on = False
LIMITE = 7  # cm

# previous state to detect changes and publish commands to the Arduino
previous_detect_state = False

# -- LED inactivity watchdog
last_dist_msg_time = 0.0
previous_led_state = None  # None/True/False
INACTIVITY_TIMEOUT = 3.0  # seconds without messages on TOPIC_DISTANCIA -> turn LED off

last_face = 0
last_state = None
COOLDOWN = 2.0  # seconds

MODEL_FILE = "face_model.yml"
LABELS_FILE = "labels.pkl"

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

# load label map (name -> int), we reverse it for int->name
with open(LABELS_FILE, "rb") as f:
    name_to_label = pickle.load(f)
label_to_name = {v:k for k,v in name_to_label.items()}

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_FILE)

# Loading the cascade for face detection
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# ===================== MQTT =====================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC_DISTANCIA)
        print("[MQTT] connected, subscribe to distance")
    else:
        print("[MQTT] rc:", rc)

def on_message(client, userdata, msg):
    global detect_on, previous_detect_state, last_dist_msg_time, previous_led_state
    try:
        data = json.loads(msg.payload.decode())
        print(data)
        dist_val = data.get("distancia_cm")
        if dist_val is not None:
            write_to_influx(
                measurement="mqtt_logs",
                tags={"topic": msg.topic, "direction": "incoming"},
                fields={"distancia_cm": float(dist_val)}
            )
        # update detect_on as before (used for face detection loop)
        new_detect = data.get("distancia_cm", 9999) < LIMITE
        detect_on = new_detect

        # update last received time for distance messages
        last_dist_msg_time = time.time()

        # on each received distance message, publish {"led": true} (avoid repeat publishes)
        try:
            if previous_led_state is not True:
                led_msg = {"led": True}
                client.publish(TOPIC_LED, json.dumps(led_msg))
                previous_led_state = True
                print(f"[MQTT] LED -> {led_msg} on {TOPIC_LED}")
        except Exception as e:
            print("[MQTT] error publishing LED:", e)
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

# ===================== FACE DETECTION AND RECOGNITION =====================
def detect():
    global cap, last_face, last_state
    if cap is None:
        cap = cv2.VideoCapture(URL)
        if not cap.isOpened():
            print("[ERROR] Unable to open the video stream")
            return

    ret, frame = cap.read()
    if not ret:
        return

    # rotation if needed
    try:
        frame = cv2.rotate(frame, cv2.ROTATE_180)
    except Exception:
        pass

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
    now = time.time()
    face_detected = False

    for (x,y,w,h) in detected:
        # ignore very small faces
        if w < 30 or h < 30:
            continue

        face_roi = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_roi, (200,200))

        # predict
        label, confidence = recognizer.predict(face_resized)
        # LBPH: lower confidence = better match. Adjust the threshold according to tests (e.g., 50..80)
        THRESH = 110.0
        name = "Unknown"
        if confidence <= THRESH and label in label_to_name:
            name = label_to_name[label]
            face_detected = True
            if last_state != True:
                msg = {
                    "authorization": True,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "confidence": float(confidence)
                }
                client.publish(TOPIC_ROSTRO, json.dumps(msg))
                last_state = True
        # draw
        try:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0) if name!="Unknown" else (0,0,255), 2)
            cv2.putText(frame, f"{name} ({int(confidence)})", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0) if name!="Unknown" else (0,0,255), 2)
        except Exception:
            pass

    # no face recognized -> publish False after cooldown
    if not face_detected and (now - last_face > COOLDOWN) and last_state != False:
        msg = {"authorization": False, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        client.publish(TOPIC_ROSTRO, json.dumps(msg))
        last_state = False

    if face_detected:
        last_face = now

    # display (if there's no Qt backend, we ignore the error and continue headless)
    try:
        cv2.imshow("Cam", frame)
    except cv2.error as e:
        # no GUI available (Wayland/Qt) -> we ignore it
        pass

# ===================== LOOP =====================
try:
    while True:
        # LED inactivity watchdog: if no distance messages received recently, send {"led": false}
        now = time.time()
        try:
            if last_dist_msg_time != 0 and (now - last_dist_msg_time) > INACTIVITY_TIMEOUT:
                if previous_led_state is not False:
                    led_msg = {"led": False}
                    client.publish(TOPIC_LED, json.dumps(led_msg))
                    previous_led_state = False
                    print(f"[MQTT] LED -> {led_msg} on {TOPIC_LED} (inactivity)")
        except Exception as e:
            print("[MQTT] error publishing LED inactivity:", e)

        if detect_on:
            detect()
        else:
            time.sleep(0.5)
        # keyboard management if GUI is available
        try:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception:
            # no GUI -> we continue
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
