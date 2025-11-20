import cv2
import paho.mqtt.client as mqtt
import time

# Configuración de la conexión MQTT
mqtt_broker = 'totox.local'  # Cambia esto por la IP o dirección de tu broker MQTT
mqtt_port = 8883  # Puerto del broker MQTT (asegurando que estás usando el puerto correcto)
mqtt_topic = 'sensor/rostro'  # Tema donde publicamos el mensaje

# Rutas a los certificados
ca_cert = 'ca.crt'  # Archivo de certificado de la CA
client_cert = 'server.crt'  # Archivo de certificado del cliente
client_key = 'server.key'  # Archivo de clave privada del cliente

# Crear un cliente MQTT
client = mqtt.Client()

# Función de conexión MQTT
def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código {rc}")
    if rc == 0:
        client.subscribe(mqtt_topic)
    else:
        print("Error al conectar al broker.")

# Asignar la función de conexión
client.on_connect = on_connect

# Configuración de SSL/TLS para la conexión segura (solo una vez)
#client.tls_set(certfile=client_cert, keyfile=client_key, cafile=ca_cert)  # Establece los certificados
client.tls_set(certfile=client_cert, keyfile=client_key, ca_certs=ca_cert)  # Establece los certificados


# Conectar al broker MQTT
print("Conectando al broker MQTT...")
client.connect(mqtt_broker, mqtt_port, 60)

# Iniciar el bucle de MQTT
client.loop_start()

# Cargar el clasificador de rostros
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

url = 'http://172.21.17.202:81/stream' 

cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo obtener la imagen de la cámara.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # Si se detectan rostros, enviar un mensaje MQTT
    if len(faces) > 0:
        print("¡Rostro detectado!")
        client.publish(mqtt_topic, 'Rostro detectado')
        # Dibujar rectángulos alrededor de los rostros detectados
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 4)

    # Mostrar la imagen con los rostros detectados
    cv2.imshow('Face Detection', frame)

    # Salir si se presiona la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(1)  # Esperar 1 segundo antes de volver a intentar

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
