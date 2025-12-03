# influx_handler.py

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

# Initialisation InfluxDB (Gestion des erreurs de connexion)
try:
    if not INFLUX_URL or not INFLUX_TOKEN or not INFLUX_ORG or not INFLUX_BUCKET:
        raise ValueError("Variables d'environnement InfluxDB non configurées.")
        
    client_influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client_influx.write_api(write_options=SYNCHRONOUS)
    print("[INFLUX] Connexion établie.")

    def write_to_influx(measurement, tags, fields):
        """Écrit un point de donnée dans InfluxDB."""
        try:
            p = Point(measurement)
            for key, value in tags.items():
                p.tag(key, value)
            for key, value in fields.items():
                p.field(key, value)
                
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
        except Exception as e:
            print(f"[INFLUX] Erreur d'écriture: {e}")

except Exception as e:
    print(f"[ERROR] Échec de la connexion à InfluxDB: {e}")
    # Définir une fonction factice si la connexion échoue
    def write_to_influx(measurement, tags, fields):
        pass
    print("[WARN] InfluxDB désactivé. Les logs de la base de données seront ignorés.")