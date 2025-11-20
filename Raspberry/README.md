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