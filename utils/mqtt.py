import asyncio
import requests
from agent.tools.devices_tools import init_db_if_needed
from repository.projects import get_phone_by_asha_id

FRONTEND_SENSOR_URL = "http://localhost:3000/asha/sensor-trigger"

_event_loop: asyncio.AbstractEventLoop | None = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _event_loop
    _event_loop = loop


async def _resolve_phone(asha_id: str) -> str | None:
    await init_db_if_needed()
    return await get_phone_by_asha_id(asha_id)


def check_ashaID_return_userNumber(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")
    asha_id = topic.split("/")[-1]

    try:
        future = asyncio.run_coroutine_threadsafe(_resolve_phone(asha_id), _event_loop) # noqa
        phone = future.result(timeout=5)
    except Exception as e:
        print(f"[MQTT] Error resolving phone for {asha_id}: {e}")
        return

    if not phone:
        print(f"[MQTT] No phone number found for ashaID: {asha_id}")
        return

    requests.post(FRONTEND_SENSOR_URL, json={
        "phone": phone,
        "sensor_data": payload,
    })
