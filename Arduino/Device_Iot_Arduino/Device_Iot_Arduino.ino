#include <WiFi.h>
#include <ArduinoJson.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "time.h" // Para sincronización NTP

// ===================== CONFIGURACIÓN Wi-Fi y MQTT =====================
const char* ssid = "Totox";
const char* password = "caca1919";
const char* mqtt_server = "totox.local"; // Dirección o IP del broker
const int mqtt_port = 8883;

// Tópicos MQTT
const char* topic_rostro = "sensor/rostro";      // Para recibir mensaje de detección facial
const char* topic_distancia = "sensor/distancia"; // Para enviar mensaje cuando alguien está cerca

// ===================== CERTIFICADOS (Mutua Autenticación) =====================

const char* ca_cert = \
"-----BEGIN CERTIFICATE-----\n" \
"MIIFCTCCAvGgAwIBAgIULdSVvYRBWJEOBOAS6C652y35a1EwDQYJKoZIhvcNAQEL\n" \
"BQAwFDESMBAGA1UEAwwJTXlNUVRULUNBMB4XDTI1MTEwNzIzMjU0MloXDTM1MTEw\n" \
"NTIzMjU0MlowFDESMBAGA1UEAwwJTXlNUVRULUNBMIICIjANBgkqhkiG9w0BAQEF\n" \
"AAOCAg8AMIICCgKCAgEA05vtdVpbELZMPvcY8YMO5irlf1MwtzX4h5OxR5czmtr6\n" \
"IYTD/Vcpd8BFjrxhv48YTTVEzVEdyxuuMWhT0uwAN1Tr7cZYdKhhQakdDzCjgcOW\n" \
"M5nOI34tlZ4L3MsOzqh463lWknU7/Ihq088wn1tE0//C87LzXPOp4BR7IIjsmvdK\n" \
"s31bqweLvWY/f6NNIWA5M3ckaITpBsASIYx8AEunqyb6qRyt9w/PstThJcqd9O9o\n" \
"ebHJMyEMQNjlQ0JrCFIhkDafNF1a/sKOU/ozU2n58d7+J577qxM9i7BIe4H4vWEl\n" \
"DsAGgifF4s7oBZI0KYqeSWUsUjvaPy8Z6vBeJTNznssKvRkac4Jt5WfO24GQz9On\n" \
"4qZXkpr3/b7wEE/mXeQnl6ZjEUB7FX+TEr+jwMgbsIMZH/x+cHkgXYdT1p8niEh1\n" \
"wge6KwVJqnrEdXz6SS56A4gtIh9RCVpEgNVBUepy0Kxmbi6yOE2G50xrZbacN3RW\n" \
"V7Id7JFGK0QekTUVmnXXRaii6j8mCO1s8o+PlFL5wuxmuRFUqngEyctz/4ozwNHC\n" \
"5kEu2QwVwVIQuGXQEOum+a6LCE1Dk/yTHj0c03deZ63VuRcQacGyqV/niEHxckgX\n" \
"po0fHghQNarQcyjfJ368KINah9VD6rJm0Rcz2SWazQzbRBVE3v5gQYP/nZYoI0cC\n" \
"AwEAAaNTMFEwHQYDVR0OBBYEFNIw18JL/ZbPkkTLolwycOPp4EMyMB8GA1UdIwQY\n" \
"MBaAFNIw18JL/ZbPkkTLolwycOPp4EMyMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZI\n" \
"hvcNAQELBQADggIBAM/FahYtOtxB7T4CIHEpIMPJLXVMPChnpQOB11XzUhmUehdQ\n" \
"sLsP1QsHAGjlYNS+KN3lBePd105K1DzLtvNydKqjfHoPtxrRevJUjbt3xNMvqgXb\n" \
"9x3qVKEF1s++BcY+DFUV8yDGmQZzeOvPr9kjSw63iH1IJKFTZ/ra3JqMCF7BkcLN\n" \
"hSiXVJOHXdkAaxK5Frjil7RLdYwTxnZec7jjENV8dFJBgJWeAfDBG07zI90MqYXj\n" \
"q+VBQ+g/GwVf7+Zjt7UPvX1XzJehTrCKw/gVhVnqTwGsdue5t+oXVmsqYFFOHgtX\n" \
"r3SYhxY3muOX0Gof7ueWB5SsdTgiuN+evS5Nhw2H1vTiuDY1Nc4JsaArOHwfa16H\n" \
"4jYxbn9vrGvK+iliMJo/pfUgWqoTQn47/gWB3SyD663CYzZuyRVVu02TKAStUKeO\n" \
"tLIc1i3DvwCM8h/VNByMBft20N9lO7vt3k9VUKKYS9sYk30a1rhtUtnSxJM1gnTM\n" \
"5JvHyq9nlSiLnw/WuaB73/XStA779tX9ISxTPXUKHpZaO8XUF9rwc3E4R8gb2Y1I\n" \
"I0VZ8PhvfukhR1gZlol5/g5a82NzWLUlxxrvcjFxOFUoawTkOOTMGKXj3cQUwunK\n" \
"ER+1JgNdegGytY6IAzPN0M5P7RF2wRm6FSfOihztwyydAVcM3bcyV1lhxtVJ\n" \
"-----END CERTIFICATE-----\n" ;


const char* client_cert = \
"-----BEGIN CERTIFICATE-----\n" \
"MIID+zCCAeOgAwIBAgIUF1XjY5MzjY6GMynHa98zc5vZ+2cwDQYJKoZIhvcNAQEL\n" \
"BQAwFDESMBAGA1UEAwwJTXlNUVRULUNBMB4XDTI1MTEwNzIzMjcxM1oXDTI2MTEw\n" \
"NzIzMjcxM1owFzEVMBMGA1UEAwwMZXNwMzItY2xpZW50MIIBIjANBgkqhkiG9w0B\n" \
"AQEFAAOCAQ8AMIIBCgKCAQEAkySgA71MGslavXY7FpJNr8Q3ILCRfaEB4pYSVSpJ\n" \
"49m3RW576PM40KhzZmrf0KObOJx6l/16/z+hY4IhF+O79rPfPXbbYXNDdYwgms+I\n" \
"UNswrsFYmQ3bz6iTy5J5+ecK2A1KcHj9asUTioMLBTinZFXeu4hO3S0F4eq+DhtR\n" \
"5eWdW0U4xyWM6bBqyBIl010my4XEqzZ4wmjw5/MAZ/D5YGSXsJGkY3yQNnt7oay7\n" \
"onwEjuluDlMKr32RrpRejs7VgmtsqkiZvJjpZ9AzmDjmN/E/Dim1cLajgOu23GTa\n" \
"cuxq58AKHBRqJh9JAN1KKjHDc/hwfhQwRm+ZSsQNMUsHLQIDAQABo0IwQDAdBgNV\n" \
"HQ4EFgQUBFM7V2lqYtmNc4CwRJ+e/IgjtxowHwYDVR0jBBgwFoAU0jDXwkv9ls+S\n" \
"RMuiXDJw4+ngQzIwDQYJKoZIhvcNAQELBQADggIBAMmrI2jeMqBx4yRTRoyAmC1N\n" \
"1VQEpqi7dfUK7P3z2GkQBQslTZ7Mmqi1Um/5Hg5cV+FLp+4Ovhn73Qg05qWQjiye\n" \
"uLljQB7ObUnFsXW3wQNZ3b9zYN1z8duqprwTFjxfqBIs+TNmCf0v8g/kCRsczeCq\n" \
"7fxH+aeIP2Saphv6YH47fDd+NtDZB13c17+BKAlrtoLEFySLTPwWrPijFaUU8pb1\n" \
"/eBuhE42dFamUidxJ/Zz7CcqHy4Hn+PG0kQIJYDwHWQ4x2i3oqVUEatdCc9Lf5a0\n" \
"CYKuxr/HEeCpFyjngk21wzPYcBSBaYkIbYO0404etmBlxtoLYl4x1ZlU+0ay7bVL\n" \
"mS9oTk96RUVCbh91MJOeuj9YFnucCjTjiz4/rMpbD5T/qMyskS35tpo6g8rBgyxU\n" \
"4JEDJDKYXoK+1skmboyRtFvgYzO5a8rXgeAYyKOZs/XsVSwjumaIZKhjsnURAIJ7\n" \
"1pN00uGBbw2suBSLkFXUTRBNdqCGc+Hf/UrU4++cbhddjO9G6zlcW/hlkFJqrHCy\n" \
"+BfC3GiUT8ZdTh8KzzjynrOELj1pDOJLNYfnj6B6A2RrzsiSu0quiaePmZNd/7nb\n" \
"fQcutjIa/ZwQ5IHassf71uYhfcm75TAixv8ytqC2ni6Bi/Cr3DexKXOMHy/skzwC\n" \
"GsojdU0ZoRT+dBtay5gd\n" \
"-----END CERTIFICATE-----\n";


const char* client_key = \
"-----BEGIN PRIVATE KEY-----\n" \
"MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCTJKADvUwayVq9\n" \
"djsWkk2vxDcgsJF9oQHilhJVKknj2bdFbnvo8zjQqHNmat/Qo5s4nHqX/Xr/P6Fj\n" \
"giEX47v2s989dtthc0N1jCCaz4hQ2zCuwViZDdvPqJPLknn55wrYDUpweP1qxROK\n" \
"gwsFOKdkVd67iE7dLQXh6r4OG1Hl5Z1bRTjHJYzpsGrIEiXTXSbLhcSrNnjCaPDn\n" \
"8wBn8PlgZJewkaRjfJA2e3uhrLuifASO6W4OUwqvfZGulF6OztWCa2yqSJm8mOln\n" \
"0DOYOOY38T8OKbVwtqOA67bcZNpy7GrnwAocFGomH0kA3UoqMcNz+HB+FDBGb5lK\n" \
"xA0xSwctAgMBAAECggEANOi3BxEyw/ECSV0xmwipmZmvDvieoDNcd6rp1ajan+0h\n" \
"6vvy301R8SmZMUsdxqqFvoH5zRxO9WhecmcQ2kO/y1JbZAEQmoZ1S9fCw5f7VsOy\n" \
"Sixo3MQwdYeS+WDmrlcHPa/tw+qliRZrU+OR+2MnQbtk1z8IyJwPYPBlPbJSLR1r\n" \
"X0PcxV2FnR4VCsJ2vlUx9CnPZXQhYG0N+EnO6ahyz9gB/7dtl32l2VlmfdKrAvFb\n" \
"pL8NUAppc/fXAa/rlLQJyKvACOMoxlc2Tz5pZTHcADxLX/W5uXmwzDXJyhgi30qQ\n" \
"MVn7CdqQAUpi1eAUclOJB/OprcoT8PmOJqJYtXP7OwKBgQDJU0vZofUi/sgm6Ull\n" \
"ehQKrvQgw4/LVOVQqdg6NQ6r4jWi0sLdFyPpvnZCVz6vV3EQ686oK8N4MN3/m6aU\n" \
"cxPShXqNH0CARpS9oVX9ieo3aSa0yFijyYmZl4fjthJx7y2BPv2wCfmZonfqWZO2\n" \
"o7QqHmkL7xFWm0N5g5ggoyNPbwKBgQC7GmxF1i6rn3yGts6Z6p8Vp6Y8ivQ0nE2l\n" \
"q6iIfWye2GOc4b8Zb9LHFKJrA+dB7JqQaQbszq2w4BB1DsN5T5c+iH2xQ4br9yCQ\n" \
"7gR9NEQ67XG988lZOrkD6ovDjRyTSjFG1cI5ASgmmjZzC+pZpYFyNcWa2UPC+uBw\n" \
"GXeB5rYFIwKBgB9xvxsSzLLWkHRjY29SDedNRBwJ71+WtupOXNNajhwSjMYNnRnj\n" \
"D1zmvpnF/qhsQ+Ccs/5YN4OCPmo56V6uSp5K8sUv6GcgnwKvPDsJW2ekKMN7tzx9\n" \
"sdwnarYKLf9VmAnjyMPCCxYP5iLYMtYH44/giA+xG0gnn/ZOs2gFkvJJAoGBAJA0\n" \
"gkSlGl1eU6zEkqGgajJXf1FkS2mNGm9YyVFBUglvf/73IsFpJUwZBEF0xbVStaId\n" \
"wJ+df9M2Lpj54wDJrikdK7sG76NIWgo52K3jLb85KJQdpA8oqlZxXH1Acki3Qxl0\n" \
"QPiMgrSV4Od0xI+JdyZeeUmqsIZDs93SUwCEn79/AoGBAKD3jbUIpZVF6MSzURpf\n" \
"mzhspnzXrYndvMFJuVttj0/OuLI36ARH/k6LFEYtBqGQKYTEZ0i6oN0MvL27jBxS\n" \
"ytCw2GK93WwpoldC7oP2gGsUkOxs4VZ3cDq8SNkOyY0+IOMILkxmj0geG2OF7Ahn\n" \
"ZzB8eva/t+cxJApUtyzXD+E2\n" \
"-----END PRIVATE KEY-----\n";


// ===================== OBJETOS GLOBALES =====================

WiFiClientSecure espClient;
PubSubClient client(espClient);


// ===================== PINES =====================
const int ledGreen = 2;   // LED ok
const int ledRed   = 4;   // LED deny
const int trigPin  = 5;
const int echoPin  = 18;
const int relayPin = 14;
const int buzzerPin = 15;

// ===================== FUNCIONES =====================

// --- Conectar a la red Wi-Fi ---
void setup_wifi() {
  Serial.print("Conectando a Wi-Fi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
}

// --- Sincronizar hora mediante NTP ---
void syncTime() {
  configTime(-5*3600, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("Sincronizando hora");
  time_t now = time(nullptr);
  while (now < 8 * 3600 * 2) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("\nHora sincronizada");
}

// --- Callback: maneja los mensajes recibidos por MQTT ---
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print(topic);
  Serial.print(" | Mensaje JSON recibido: ");
  Serial.println(message);

  StaticJsonDocument<256> doc;
  deserializeJson(doc, message);

  bool autorizacion = doc["autorizacion"];
  String hora = doc["hora"] | "inconnue";

  if (autorizacion) {
    digitalWrite(ledGreen, HIGH);
    digitalWrite(ledRed, LOW);
    digitalWrite(relayPin, HIGH);
    soundGranted();
    delay(1500);
    digitalWrite(relayPin, LOW);
    digitalWrite(ledGreen, LOW);
  } else {
    digitalWrite(ledRed, HIGH);
    digitalWrite(ledGreen, LOW);
    digitalWrite(relayPin, LOW);
    soundDenied();
    delay(1000);
    digitalWrite(ledRed, LOW);
  }
}

// --- Reconexión al broker MQTT ---
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting MQTT...");
    if (client.connect("ESP32S3Client")) {
      client.subscribe(topic_rostro);
      Serial.println("Subscribed to sensor/rostro");
    } else {
      Serial.print("Fail, rc=");
      Serial.println(client.state());
      delay(4000);
    }
  }
}


// --- Obtener hora actual en formato legible ---
String obtenerHora() {
  time_t now = time(nullptr);
  struct tm* t = localtime(&now);
  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", t);
  return String(buffer);
}

// --- Medir distancia usando el sensor ultrasónico ---
float medirDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2; // Conversión a centímetros
}

// --- Publicar datos de detección al broker ---
void publicarDeteccion(float distancia) {
  StaticJsonDocument<256> doc;
  doc["evento"] = "persona_detectada";
  doc["distancia_cm"] = distancia;
  doc["timestamp"] = obtenerHora();

  char buffer[256];
  serializeJson(doc, buffer);
  client.publish(topic_distancia, buffer);

  Serial.print("Mensaje JSON publicado: ");
  Serial.println(buffer);
}

// ======== SOUND FX ========
void soundGranted() {
  tone(buzzerPin, 1000, 200); delay(200);
  tone(buzzerPin, 1500, 200); delay(200);
  noTone(buzzerPin);
}

void soundDenied() {
  tone(buzzerPin, 400, 700); delay(700);
  noTone(buzzerPin);
}

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  pinMode(ledGreen, OUTPUT);
  pinMode(ledRed, OUTPUT);
  pinMode(relayPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  setup_wifi();
  syncTime();

  espClient.setCACert(ca_cert);
  espClient.setCertificate(client_cert);
  espClient.setPrivateKey(client_key);

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  reconnect();
}

// ===================== LOOP =====================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float distancia = medirDistancia();
  publicarDeteccion(distancia);

  delay(5000); // Espera entre mediciones
}