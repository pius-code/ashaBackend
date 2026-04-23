from pydantic import BaseModel
from typing import List


class DeviceInfo(BaseModel):
    id: int
    pin: int
    category: str
    type: str
    metadata: str
    signal: str


class AshaVerificationRequest(BaseModel):
    auth_id: str
    devices: List[DeviceInfo]
