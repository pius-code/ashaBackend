import paho.mqtt.client as mqtt

# TODO: move these to env
client = mqtt.Client()
client.connect("10.235.41.41", 1883)
client.loop_start()
