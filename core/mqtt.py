import paho.mqtt.client as mqtt
import os
import ssl
from dotenv import load_dotenv

load_dotenv()

port = os.getenv("MQTT_PORT", "8883")
ip = os.getenv("MQTT_IP", "d1fb95ffc6654d6e98effc66d26fed74.s1.eu.hivemq.cloud") # noqa
username = os.getenv("MQTT_USER", "ashaESP")
password = os.getenv("MQTT_PASSWORD", "ashatheworldtothefuture")

client = mqtt.Client()
client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
client.username_pw_set(username, password)

client.connect(ip, int(port))
client.subscribe("asha/ashaSensor/+")
client.loop_start()
