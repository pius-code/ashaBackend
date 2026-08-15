from beanie import Document
from typing import List, Optional
from pydantic import BaseModel


class DeviceInfo(BaseModel):
    device_id: int
    pin: int
    category: str
    metadata: str
    bus: str
    sck: Optional[int] = None
    miso: Optional[int] = None
    mosi: Optional[int] = None
    cs: Optional[int] = None


class AshaDevice(Document):
    auth_id: str  # mac address of the esp32
    asha_id: str  # the asha string that links to a project
    pairing_code: str | None = None  # links to Project.PairingCode
    devices: List[DeviceInfo]

    class settings:
        name = "asha_devices"
