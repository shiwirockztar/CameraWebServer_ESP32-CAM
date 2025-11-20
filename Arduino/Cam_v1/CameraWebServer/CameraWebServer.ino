#include "esp_camera.h"
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "board_config.h"

// ===========================
// WiFi credentials
// ===========================
const char *ssid = "abc";
const char *password = "";

// ===========================
// MQTT (mTLS)
// ===========================
const char *mqtt_server = "totox.local";
const int mqtt_port = 8883;
const char *topic_distancia = "sensor/distancia";
const char *topic_led = "actuator/led";

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



// ===========================
// LED pins
// ===========================
const int LED1 = 18;
const int LED2 = 19;
const int LED3 = 21;
// LED físico que controlará el mensaje desde MQTT (pin 5)
const int LED_PIN = 5;

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
  // Si el mensaje viene para controlar el LED del pin 5
  if (strcmp(topic, topic_led) == 0) {
    bool led_state = false;
    // intentamos parsear JSON {"led": true}
    StaticJsonDocument<128> doc_led;
    DeserializationError err_led = deserializeJson(doc_led, message);
    if (!err_led) {
      if (doc_led.containsKey("led")) {
        led_state = doc_led["led"];
      } else if (doc_led.containsKey("state")) {
        led_state = doc_led["state"];
      }
    } else {
      // si no es JSON, aceptar valores simples: "1","0","true","false"
      if (message.equals("1") || message.equalsIgnoreCase("true")) led_state = true;
      else led_state = false;
    }
    digitalWrite(LED_PIN, led_state ? HIGH : LOW);
    Serial.printf("[MQTT] Topic %s -> LED_PIN %d %s\n", topic, LED_PIN, led_state?"ON":"OFF");
    return;
  }

  // Si el mensaje es de distancia, mantenemos la lógica existente
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
        // suscribirse también al topic que controla el LED en el pin 5
        client.subscribe(topic_led);
        Serial.printf("Abonné à %s\n", topic_led);
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
  // pin para LED controlado por MQTT (pin 5)
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED1, LOW);
  digitalWrite(LED2, LOW);
  digitalWrite(LED3, LOW);
  digitalWrite(LED_PIN, LOW);

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
