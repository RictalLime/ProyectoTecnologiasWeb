import paho.mqtt.client as mqtt
import time
import random
import json

# Configuración del broker MQTT
BROKER = "broker"  # nombre del contenedor o IP
PORT = 1883
TOPIC = "huerto/temperatura"

# Crear cliente MQTT
client = mqtt.Client()

def conectar_mqtt():
    client.connect(BROKER, PORT, 60)
    print(f"Conectado a broker MQTT en {BROKER}:{PORT}")

def publicar_dato():
    while True:
        temperatura = round(random.uniform(20.0, 35.0), 2)  # Temperatura simulada
        payload = {
            "sensor_id": "sensor_1",
            "temperatura": temperatura
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"Publicado en {TOPIC}: {payload}")
        time.sleep(5)  # espera 5 segundos

if __name__ == "__main__":
    conectar_mqtt()
    publicar_dato()
