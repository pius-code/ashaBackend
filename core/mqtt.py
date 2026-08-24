import paho.mqtt.client as mqtt
import os
import ssl
from dotenv import load_dotenv
from utils.logger import tlogger

load_dotenv()

port = os.getenv("MQTT_PORT", "8883")
ip = os.getenv("MQTT_IP", "d1fb95ffc6654d6e98effc66d26fed74.s1.eu.hivemq.cloud")  # noqa
username = os.getenv("MQTT_USER", "ashaESP")
password = os.getenv("MQTT_PASSWORD", "ashatheworldtothefuture")

def on_connect(client, userdata, flags, rc):
    tlogger.info(f"MQTT on_connect callback: rc={rc}")

def on_disconnect(client, userdata, rc):
    tlogger.warning(f"MQTT on_disconnect callback: rc={rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
client.username_pw_set(username, password)
client.reconnect_delay_set(min_delay=1, max_delay=120)
