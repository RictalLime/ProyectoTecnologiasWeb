import paho.mqtt.client as mqtt
import sqlite3
import json
from datetime import datetime

# Configuración del broker MQTT
BROKER = "broker"
PORT = 1883
TOPIC = "huerto/temperatura"
DB_PATH = "/data/sensor_data.db"  # montar volumen de Docker aquí

# Callback cuando se conecta al broker
def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código: {rc}")
    client.subscribe(TOPIC)

# Callback cuando se recibe un mensaje
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    temperatura = payload["temperatura"]
    sensor_id = payload.get("sensor_id", "desconocido")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[MQTT] {timestamp} | Sensor: {sensor_id} | Temp: {temperatura}")

    # Guardar en base de datos
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO temperaturas (sensor_id, temperatura, fecha) VALUES (?, ?, ?)",
              (sensor_id, temperatura, timestamp))
    conn.commit()
    conn.close()

# Configurar cliente MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Conectar al broker y esperar mensajes
client.connect(BROKER, PORT, 60)
client.loop_forever()
