## Entorno virtual y dependencias (opcional)

Si deseas preparar un entorno de Python para ejecutar scripts auxiliares (por ejemplo, procesamiento de imágenes o detección), puedes crear y activar un entorno virtual en Windows desde la raíz del proyecto.

En cmd.exe (ejemplo exacto que ejecutaste):

```cmd
D:\Users\SHIIWITOCKZRAT\Documents\CameraWebServer_ESP32-CAM>python -m venv venv
:: Crear el entorno virtual
D:\Users\SHIIWITOCKZRAT\Documents\CameraWebServer_ESP32-CAM>.\venv\Scripts\activate
:: Activar el entorno virtual (cmd.exe)
```

Nota: en PowerShell la activación es `.\\venv\\Scripts\\Activate.ps1`.

Una vez activado, instala las dependencias necesarias con:

```cmd
pip install ultralytics opencv-python numpy
```

Estas dependencias son útiles si vas a ejecutar modelos (por ejemplo, con Ultralytics) o scripts que procesen imágenes desde la cámara.

### Ejecutar el detector (ejemplo)

Con el entorno virtual activado, puedes ejecutar el script de detección contra el stream del ESP32-CAM. Por ejemplo (en cmd.exe):

```cmd
esp32 cam
.\detect-esp32cam.py --url http://192.168.1.144:81/stream --show
esp32 s3 cam
.\detect-esp32cam.py --url http://192.168.1.86:81/stream --show
```

Esto abrirá el visor y mostrará el resultado en pantalla si el script `detect-esp32cam.py` está presente y es ejecutable.

.\venv\Scripts\activate
pip uninstall opencv-python opencv-python-headless -y
pip install opencv-python

$ git reset --soft HEAD~1


## Modo de uso en Raspberry

- **Requisitos:** Raspberry Pi con `NetworkManager` instalado (proporciona `nmcli`), interfaz Wi‑Fi `wlan0` disponible y permisos de `sudo`.

- **Modo portal (hotspot):** se creó un alias para crear una red Wi‑Fi local (portal) que facilita pruebas sin depender de una red externa. Añade el alias a tu `~/.bash_aliases` o `~/.bashrc` para tenerlo disponible en cada sesión:

```
alias hotspot='sudo nmcli device wifi hotspot ifname wlan0 ssid RaspbeRed band bg password "12345678"'
```

- **Uso rápido:** en una terminal ejecuta `hotspot` (o `source ~/.bash_aliases` si acabas de añadirlo) y el Pi creará la red `RaspbeRed` con la contraseña `12345678`.

- **Notas de seguridad:** la contraseña mostrada es un ejemplo. Cámbiala por una contraseña segura antes de exponer la red en entornos no controlados.

- **Conectar el ESP32‑CAM o tu equipo de pruebas:** conecta el ESP32‑CAM (si está configurado como STA) o tu ordenador/telefono a la red `RaspbeRed`. Una vez conectado, podrás acceder al servidor web del ESP32‑CAM usando la IP que reciba desde el hotspot (por ejemplo `http://192.168.8.1:81/stream` o la IP asignada al dispositivo). Usa `ip addr` o `nmcli device show wlan0` para inspeccionar direcciones si es necesario.

- **Hacer el alias persistente (opcional):** edita `~/.bash_aliases` y pega la línea del alias; luego ejecuta `source ~/.bash_aliases` o abre una nueva sesión para usar `hotspot` automáticamente.