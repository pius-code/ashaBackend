from beanie import Document
from typing import List
from pydantic import BaseModel


class DeviceInfo(BaseModel):
    device_id: int
    pin: int
    category: str
    metadata: str
    bus: str


class AshaDevice(Document):
    auth_id: str
    devices: List[DeviceInfo]

    class settings:
        name = "asha_devices"
