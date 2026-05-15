import paho.mqtt.client as mqtt

# TODO: move these to env
client = mqtt.Client()
client.connect("MQTT SERVER", "MQTT PORT")
client.loop_start()
