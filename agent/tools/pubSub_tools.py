from core.mqtt import client
import json


def publish_to_device(asha_id: str, payload: dict):
    topic = f"asha/commands/{asha_id}"
    client.publish(topic, json.dumps(payload))
    print("something shoulda happebed")


