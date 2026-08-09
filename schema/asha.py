from pydantic import BaseModel
from typing import List, Optional


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


class AshaVerificationRequest(BaseModel):
    auth_id: str
    devices: List[DeviceInfo]
