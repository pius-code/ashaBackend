import paho.mqtt.client as mqtt

# TODO: move these to env
client = mqtt.Client()
client.username_pw_set("Piusasha", "Piuspius27")
client.tls_set()
client.connect("d1fb95ffc6654d6e98effc66d26fed74.s1.eu.hivemq.cloud", 8883)
