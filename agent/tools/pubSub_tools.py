from core.mqtt import client
import json
from utils.logger import tlogger


def publish_to_device(asha_id: str, payload: dict):
    topic = f"asha/commands/{asha_id}"
    result = client.publish(topic, json.dumps(payload))
    tlogger.info(f"publish rc={result.rc} is_connected={client.is_connected()}")


