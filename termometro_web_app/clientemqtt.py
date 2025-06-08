# clientemqtt.py
import paho.mqtt.client as mqtt
from queue import Queue
import threading

# Cola para compartir mensajes con app.py
mqtt_queue = Queue()

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT con código: " + str(rc))
    client.subscribe("sensor/temperatura")

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Recibido en {msg.topic}: {payload}")
    mqtt_queue.put(payload)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mosquitto", 1883, 60)

    # Ejecutar el cliente en un hilo separado
    thread = threading.Thread(target=client.loop_forever)
    thread.daemon = True
    thread.start()
