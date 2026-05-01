from pydantic import BaseModel
from typing import List


class DeviceInfo(BaseModel):
    device_id: int
    pin: int
    category: str
    metadata: str
    bus: str


class AshaVerificationRequest(BaseModel):
    auth_id: str
    devices: List[DeviceInfo]
