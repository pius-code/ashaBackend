import os
import ssl
import uuid
import certifi
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from utils.logger import tlogger

load_dotenv()

port = int(str(os.getenv("MQTT_PORT", "8883")).strip())
ip = str(os.getenv("MQTT_IP", "d1fb95ffc6654d6e98effc66d26fed74.s1.eu.hivemq.cloud")).strip() # noqa
username = str(os.getenv("MQTT_USER", "ashaESP")).strip()
password = str(os.getenv("MQTT_PASSWORD", "ashatheworldtothefuture")).strip()


def on_connect(client, userdata, flags, rc):
    tlogger.info(f"MQTT on_connect callback: rc={rc}")


def on_disconnect(client, userdata, rc):
    tlogger.warning(f"MQTT on_disconnect callback: rc={rc}")


# Unique client ID per machine/run to prevent HiveMQ kicking older connections
machine_id = os.getenv("FLY_MACHINE_ID", str(uuid.uuid4())[:8])
client_id = f"asha_backend_{machine_id}"

client = mqtt.Client(client_id=client_id)
client.on_connect = on_connect
client.on_disconnect = on_disconnect

# Set TLS using certifi's CA bundle and TLS client protocol
client.tls_set(
    ca_certs=certifi.where(),
    tls_version=ssl.PROTOCOL_TLS_CLIENT,
)

client.username_pw_set(username, password)
client.reconnect_delay_set(min_delay=1, max_delay=120)
