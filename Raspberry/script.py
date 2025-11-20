import cv2
import paho.mqtt.client as mqtt
import time, json
from datetime import datetime

# ===================== CONFIG MQTT =====================
BROKER = "totox.local"
PORT = 8883
TOPIC_ROSTRO = "sensor/rostro"
TOPIC_DISTANCIA = "sensor/distancia"
CA = "ca.crt"
CERT = "server.crt"
KEY = "server.key"

# ===================== VARIABLES =====================
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
#url = "http://172.21.17.202:81/stream"
url = "http://192.168.40.26:81/stream"
cap = None
detect_on = False
LIMITE = 50  # cm

ultimo_rostro = 0
ultimo_estado = None  # memoriza si ya enviamos True o False
COOLDOWN = 2.0  # segundos

# ===================== MQTT =====================
def on_connect(client, userdata, flags, rc):
    if rc == 0: client.subscribe(TOPIC_DISTANCIA)

def on_message(client, userdata, msg):
    global detect_on
    try:
        data = json.loads(msg.payload.decode())
        detect_on = data.get("distancia_cm", 9999) < LIMITE
    except: pass

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY)
client.connect(BROKER, PORT, 60)
client.loop_start()

# ===================== DETECCIÓN =====================
def detectar():
    global cap, ultimo_rostro, ultimo_estado
    if cap is None:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return

    ret, frame = cap.read()
    if not ret:
        return

    frame = cv2.rotate(frame, cv2.ROTATE_180)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.2, minNeighbors=7, minSize=(100, 100)
    )

    now = time.time()
    rostro_detectado = len(faces) > 0

    if rostro_detectado:
        ultimo_rostro = now
        if ultimo_estado != True:
            msg = {
                "autorizacion": True,
                "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.publish(TOPIC_ROSTRO, json.dumps(msg))
            ultimo_estado = True

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

    else:
        if (now - ultimo_rostro > COOLDOWN) and ultimo_estado != False:
            msg = {
                "autorizacion": False,
                "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            client.publish(TOPIC_ROSTRO, json.dumps(msg))
            ultimo_estado = False

    cv2.imshow("Cam", frame)

# ===================== LOOP =====================
try:
    while True:
        if detect_on: detectar()
        else: time.sleep(0.5)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
except KeyboardInterrupt:
    pass
finally:
    if cap: cap.release()
    cv2.destroyAllWindows()
    client.loop_stop()
    client.disconnect()
