import asyncio
import requests
from agent.tools.devices_tools import init_db_if_needed
from repository.projects import get_phone_by_asha_id

FRONTEND_SENSOR_URL = "http://localhost:3000/sensor-trigger"


async def _resolve_phone(asha_id: str) -> str | None:
    await init_db_if_needed()
    return await get_phone_by_asha_id(asha_id)


def check_ashaID_return_userNumber(client, userdata, message):
    topic = message.topic
    payload = message.payload.decode("utf-8")
    asha_id = topic.split("/")[-1]

    phone = asyncio.run(_resolve_phone(asha_id))
    if not phone:
        print(f"[MQTT] No phone number found for ashaID: {asha_id}")
        return

    requests.post(FRONTEND_SENSOR_URL, json={
        "phone": phone,
        "asha_id": asha_id,
        "sensor_data": payload,
    })
