import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
load_dotenv()

port = os.getenv("MQTT_PORT")
ip = os.getenv("MQTT_IP")
client = mqtt.Client()
client.connect(ip, int(port))
client.loop_start()
