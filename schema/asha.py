from pydantic import BaseModel
from typing import List
from model.asha_device import DeviceInfo


class AshaVerificationRequest(BaseModel):
    project_name: str
    mac_address: str
    devices: List[DeviceInfo]


class ashaDeviceSchema(BaseModel):
    auth_id: str
    asha_id: str
    pairing_code: str | None = None
    devices: List[DeviceInfo]


class PairingCodeCheckRequest(BaseModel):
    pairing_code: str


class UncommissionRequest(BaseModel):
    pairing_code: str


class ClaimDeviceRequest(BaseModel):
    pairing_code: str
    channel: str | None = None
    address: str | None = None
