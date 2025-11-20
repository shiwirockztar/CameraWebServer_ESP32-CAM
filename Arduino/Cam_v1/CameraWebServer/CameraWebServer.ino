#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "board_config.h"

// ===========================
// WiFi credentials
// ===========================
const char *ssid = "Totox";
const char *password = "caca1919";

// ===========================
// MQTT (mTLS)
// ===========================
const char *mqtt_server = "totox.local";
const int mqtt_port = 8883;
const char *topic_distancia = "sensor/distancia";

// ===========================
// Certificats mTLS
// ===========================
// (⚠️ Copie bien le contenu exact de tes fichiers ici)
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
"-----END CERTIFICATE-----\n";

const char* client_cert = \
"-----BEGIN CERTIFICATE-----\n" \
"MIID/DCCAeSgAwIBAgIUF1XjY5MzjY6GMynHa98zc5vZ+2gwDQYJKoZIhvcNAQEL\n" \
"BQAwFDESMBAGA1UEAwwJTXlNUVRULUNBMB4XDTI1MTEwNzIzMzQwMloXDTI2MTEw\n" \
"NzIzMzQwMlowGDEWMBQGA1UEAwwNY2FtZXJhLWNsaWVudDCCASIwDQYJKoZIhvcN\n" \
"AQEBBQADggEPADCCAQoCggEBAKSovjFpSLLdOirK8L76QOfivqurhif6JYXz0rgK\n" \
"GWrKlmVY2TugVpjw9WNN0nEHy8jsVwsaqFmV8uyhT77OTJOb1+Vo0hdq9idB8ov8\n" \
"KU61K8u/4gERPNs71Gd0reFjlmB3iW+e7SO2b2CPT3uRoNc/NyTcenQhgI5EDslj\n" \
"QGLBSLswqlRkHeuXjjrMuTIzf3EFB4WnxOMxRpCP3OqZXXTFL9St/XKdkcBiBrfL\n" \
"VcLxZXGdDiC/JGUzeDOAVrXx6u4KNRWIaUnxUBPL6klgGyDLOC33H5Rm+N9N9Vjg\n" \
"xnuiUoW8ixYTxI/E8suQQrc3kAb/5c++rOL8Uzb1XcJtdWECAwEAAaNCMEAwHQYD\n" \
"VR0OBBYEFPWaezAPhRqnUROx11PaTyRpNK37MB8GA1UdIwQYMBaAFNIw18JL/ZbP\n" \
"kkTLolwycOPp4EMyMA0GCSqGSIb3DQEBCwUAA4ICAQBl546PU2LJ+ByOO6Hgd3xR\n" \
"PhOp1nfNrJGF6Iv6gGvOlu/rDenUcAI1phEYb7Xf0gbqq18Re6rKhvvbiI2+EiQI\n" \
"ru3jtULjSq2PEm5IY9/f2urJe/JE6fdYYoQJ0mgC9KpFJKirtEVrtvZBqq3dxs5t\n" \
"MXIZe6yWOEbqlBuYOqJvs6zFRNpq5UvJ5qMIYGiLDaN29lJDNK1y4BYlUJghtMqP\n" \
"23xoRJJa+ZP6UtMPsalFv7dUot4ksx1A0RVwm5g0mcw7Cln6UTQm1Hn46HvJ1Cb5\n" \
"ELjRO69/kokra9lBHKs6bKa/kz1B3IJUyESLo1NT5TAy9ZPC0pSVYoH7Wv+kvJfL\n" \
"+toXXsXbPixoaJVDnyWTm4AVbz4Ot/O3HxxqOcXnxJrzNO+ImV/wOZT6ik7qLKpE\n" \
"CtLMpNYkx7/72gq+Aq6bqu/m2PoeMCsKKEN+EDhke/E8iFXGu4F16kbN8Qfmdpfw\n" \
"C2JFUo4rKHxGqpIJUXp5f963d2UBfUnIYoD9H0V0/i0Nj0of7beWkEB2REbDNKJX\n" \
"2L6uZ+BfRcIFegfiWq1LVorvgEb04sKy4KnyofpkrQfPXNmu3rIndEuch1wYvx+u\n" \
"PQKp79OhoxVOaJy70UIx29CD4qy9Yf0Z1d/XKaMFezMWEagaaKPxwGd2ySTcWnGd\n" \
"Djvj9t/U82yD8Qfi6n5+CQ==\n" \
"-----END CERTIFICATE-----\n";

const char* client_key = \
"-----BEGIN PRIVATE KEY-----\n" \
"MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCkqL4xaUiy3Toq\n" \
"yvC++kDn4r6rq4Yn+iWF89K4ChlqypZlWNk7oFaY8PVjTdJxB8vI7FcLGqhZlfLs\n" \
"oU++zkyTm9flaNIXavYnQfKL/ClOtSvLv+IBETzbO9RndK3hY5Zgd4lvnu0jtm9g\n" \
"j097kaDXPzck3Hp0IYCORA7JY0BiwUi7MKpUZB3rl446zLkyM39xBQeFp8TjMUaQ\n" \
"j9zqmV10xS/Urf1ynZHAYga3y1XC8WVxnQ4gvyRlM3gzgFa18eruCjUViGlJ8VAT\n" \
"y+pJYBsgyzgt9x+UZvjfTfVY4MZ7olKFvIsWE8SPxPLLkEK3N5AG/+XPvqzi/FM2\n" \
"9V3CbXVhAgMBAAECggEAAII++DMdlOPnGpu+67AlRDIoqaohg30b4ZKTy5rIYlKW\n" \
"7WA9Z5hCvD0+XNywMkY2ZHwKds/RxlkWw5FqCCpmBSy9mYld4NGlShDDmZghXotj\n" \
"w8Dnh15QxFKmgN1U7jXbEJg99fjVPb+CD5fRxI16JEAfQP9nZ3V1Crt+GjQyzjtO\n" \
"Y9NiWNTOKf8nlF8EXBcNtZ+uGkNOCaqNcloA6SbrlkFqE3tG5caIHz0SRW4EldfF\n" \
"q8nw9knVx8SiRxrBQfyJTqhaJgYnv6ksGkKb6gspVvvvPijf3Tki3DV4I2uitB0w\n" \
"0fW25sE4QsjwwemYcIJrfOFJwi+2Z1jOmLLcW7gQCwKBgQDSODp0aUc+GU78en0E\n" \
"BtNh/CV4c+iEEtbrhzF6dBG9RcvxasAQtCIGCaHqlxmy9Uk5PVLeHi0HMzdwjqsM\n" \
"Y8TH3LrFwV080PPsXLPtuG7waJG2M9jj62XjkmXvJo1Xubqs6JMwt93eFMEnSKwz\n" \
"4T1QtLtkeWuU5hMeCs8ZhOhGvwKBgQDIhILzRpMVKwGth+60ZucBa4gLCGH0XdQ1\n" \
"O14NkKjTKUh4EP0/e5HMenTgtYDx/eBpcNRMy9WpZAdZg+w4USwiMLa2R8ZTQ1yA\n" \
"4ItwrexB7FePw5v9l04YBlOsk/R2Bu/yiieh1YYoNn5eWBgTwo9tFd6P6GBA/84Z\n" \
"WljDMPpr3wKBgC5fev2dD7syKAtoFdXij5TI45crsnoYEdMJErAZlKQ1FmUeEFpe\n" \
"8jZ0v4QZavDgTRPUZEhdTb+N28f3oOHtzEXuekEPg7rbuUNFu+dPzSE5YBNaYpj8\n" \
"n5BRBi14Squ0a+qir32KweWwnF9HF72mDTmVdNUYN9Qz4Lm61q6hc//PAoGAcJNE\n" \
"2cRTq1y70mswrwPeycNPW7JXHFTZYRF1mnQO9I6G6zHOnKeJkZ1mpQoB3NrF9Syt\n" \
"ZHhD+pf4MF+KbYvVFVT4H5poVDLLamemoZpjvBcuib4ug89Avug+bfObGfCHIkpC\n" \
"Oe+hJE6D3//hdKaU04+lpnG2KIf1c/JvRxbmYU0CgYBgZ0jVL7t36DBAYEbKcv+V\n" \
"PUzHzJsNW7rN8LyZ60X5JKnyTQB4/zqGS53zMda8AZuFxt2dsCW8Ec0iWg6aAbOL\n" \
"miD56xvp5O/ZeZRj3fqIfb7uAtBByf9iP7DPJttXgv4hPGFeK7n4xITCWqse4sS/\n" \
"d+0aQlS9rle5JbfI+Jz5zQ==\n" \
"-----END PRIVATE KEY-----\n";

// ===========================
// LED pins
// ===========================
const int LED1 = 18;
const int LED2 = 19;
const int LED3 = 21;

// ===========================
// Clients WiFi + MQTT
// ===========================
WiFiClientSecure secureClient;
PubSubClient client(secureClient);

// ===========================
// Prototypes
// ===========================
void startCameraServer();
void setupLedFlash();
void reconnectMQTT();

// ===========================
// MQTT Callback
// ===========================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.printf("\n[MQTT] Message reçu sur %s : ", topic);
  String message;
  for (unsigned int i = 0; i < length; i++) message += (char)payload[i];
  Serial.println(message);

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, message);
  if (err) {
    Serial.println("Erreur JSON !");
    return;
  }

  float distance = doc["distancia_cm"]; // récupérer la distance
  if (distance < 50.0) {
    Serial.println("✅ Distance < 50cm : LEDs ON");
    digitalWrite(LED1, HIGH);
    digitalWrite(LED2, HIGH);
    digitalWrite(LED3, HIGH);
  } else {
    Serial.println("❌ Distance >= 50cm : LEDs OFF");
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);
    digitalWrite(LED3, LOW);
  }
}

// ===========================
// Reconnexion MQTT
// ===========================
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT (mTLS)...");
    if (client.connect("ESP32CAM_CLIENT")) {
      Serial.println("connecté !");
      client.subscribe(topic_distancia);
      Serial.printf("Abonné à %s\n", topic_distancia);
    } else {
      Serial.print("Échec, rc=");
      Serial.print(client.state());
      Serial.println(" => nouvelle tentative dans 5s");
      delay(5000);
    }
  }
}

// ===========================
// SETUP
// ===========================
void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // === Configuration caméra ===
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (psramFound()) {
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed 0x%x", err);
    return;
  }

  // === Ajustement du capteur ===
  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  s->set_framesize(s, FRAMESIZE_QVGA);

  // === LEDS ===
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  digitalWrite(LED1, LOW);
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  // === WiFi ===
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  Serial.print("Connexion WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connecté !");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // === Démarre le streaming ===
  startCameraServer();

  // === Config mTLS ===
  secureClient.setCACert(ca_cert);
  secureClient.setCertificate(client_cert);
  secureClient.setPrivateKey(client_key);

  // === MQTT ===
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  reconnectMQTT();

  Serial.print("Caméra prête ! Stream : http://");
  Serial.println(WiFi.localIP());
}

// ===========================
// LOOP
// ===========================
void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();
  delay(10);
}
