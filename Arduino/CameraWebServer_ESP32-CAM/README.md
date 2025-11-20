# Servidor Web Cam para ESP32-CAM (Ai Thinker)

Este repositorio contiene el código para ejecutar un servidor web de cámara usando un módulo ESP32-CAM. El proyecto está pensado para la placa "Ai Thinker ESP32-CAM" y se ha configurado para usar PSRAM.

## Placa y configuración

- Placa seleccionada: Ai Thinker ESP32-CAM
- Configuración en el código:

```c
#define CAMERA_MODEL_AI_THINKER // Has PSRAM
```

Asegúrate de seleccionar la placa correcta en el IDE de Arduino (o en tu entorno de compilación preferido) y de tener las dependencias de la ESP32 instaladas.

## Descripción

El código implementa un servidor HTTP que expone la cámara del ESP32-CAM como una página web y/o stream. Desde el navegador podrás acceder al feed de la cámara y a funciones básicas (captura de imagen, streaming, ajustes según el firmware incluido).

## Notas importantes

- La variante `AI_THINKER` suele requerir que actives PSRAM en la configuración si tu módulo la soporta.
- Verifica los pines en `camera_pins.h` y la configuración en `board_config.h` si usas un módulo no estándar o has modificado cables.
- Recomendado usar la versión más reciente del soporte ESP32 en el Gestor de Placas del IDE de Arduino.

##

https://10015.io/tools/base64-encoder-decoder:

```
MTIgTUlOVVRPUyBwYXJhIERPTUlOQVIgbGEgRVNQMzItQ0FNIHkgREVURUNUQVIgT0JKRVRPUwpodHRwczovL3d3dy55b3V0dWJlLmNvbS93YXRjaD92PTlDTXlIS3hMUmRV
```

## Cómo compilar y subir

1. Instala el soporte de placas ESP32 en el Gestor de Placas del IDE de Arduino.
2. Selecciona la placa: "AI Thinker ESP32-CAM".
3. Abre `CameraWebServer_ESP32-CAM.ino` en el IDE.
4. Configura la red Wi-Fi y otros parámetros en el código si es necesario.
5. Compila y sube al módulo.

## Contacto / Más info

El repositorio contiene los archivos principales: `CameraWebServer_ESP32-CAM.ino`, `app_httpd.cpp`, `camera_index.h`, `camera_pins.h`, `board_config.h`. Revisa esos archivos para personalizar rutas, páginas y funcionalidades del servidor.

---

Archivo generado automáticamente: README para el proyecto ESP32-CAM.
