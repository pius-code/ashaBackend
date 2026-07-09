import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
from utils.mqtt import check_ashaID_return_userNumber
load_dotenv()

port = os.getenv("MQTT_PORT")
ip = os.getenv("MQTT_IP")
client = mqtt.Client()
client.connect(ip, int(port))
client.subscribe("asha/ashaSensor/+")
client.message_callback_add("asha/ashaSensor/+", check_ashaID_return_userNumber) # noqa
client.loop_start()
