from core.mqtt import client
import json
from utils.logger import tlogger
from utils.asha_utils import gen_correlation_id
import threading

_pending = {}

def publish_to_device(asha_id: str, payload: dict, wait_response: bool = False):
    topic = f"asha/commands/{asha_id}"
    tlogger.info(payload)

    if not wait_response:
        result = client.publish(topic, json.dumps(payload))
        tlogger.info(f"publish rc={result.rc} is_connected={client.is_connected()}")
        return

    rtopic = f"asha/response/{asha_id}"
    client.subscribe(rtopic)
    payload["correlation_id"] = gen_correlation_id()
    event = threading.Event()
    _pending[payload["correlation_id"]] = {"event": event, "data": None}
    result = client.publish(topic, json.dumps(payload))
    tlogger.info(f"publish rc={result.rc} is_connected={client.is_connected()}")
    event.wait(5)
    rdata = _pending[payload["correlation_id"]]["data"]
    del _pending[payload["correlation_id"]]
    if rdata is None:
        tlogger.info(f"timeout waiting for response from {asha_id}")
        return {"status": "timeout", "asha_id": asha_id}
    tlogger.info(f"response received: {rdata}")
    return {"status": "ok", "asha_id": asha_id, "response": rdata}


def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    correlation_id = data.get("correlation_id")
    if correlation_id and correlation_id in _pending:
        _pending[correlation_id]["data"] = data
        _pending[correlation_id]["event"].set()

client.on_message = on_message
