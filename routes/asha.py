# this file is for the hardware - software communication only!


from fastapi import APIRouter, Depends, HTTPException
from schema.project import projectCreate
from schema.asha import (
    AshaVerificationRequest,
    ashaDeviceSchema,
    UncommissionRequest,
    ClaimDeviceRequest,
) # noqa
from repository.asha_repo import add_IoT_device
from utils.logger import slogger
from repository.projects import (
    create_an_asha_project,
    validate_and_commission_project,
    uncommission_project,
    get_user_projects,
) # noqa
from middleware.auth import get_current_user
from model.user import User


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])


@router.post("/verify_and_register_device")
async def verify_device(AshaIoTPayload: AshaVerificationRequest):
    slogger.info("New device being registered")
    print(AshaIoTPayload)
    project_data = projectCreate(
        Name=AshaIoTPayload.project_name,
        MacAddress=AshaIoTPayload.mac_address)

    result = await create_an_asha_project(project_data)
    device_payload = ashaDeviceSchema(
        auth_id=AshaIoTPayload.mac_address,
        asha_id=result.AshaID,
        pairing_code=result.PairingCode,
        devices=AshaIoTPayload.devices
    )
    added_device = await add_IoT_device(device_payload)
    return {
        "message": "device registered successfully.",
        "asha_id": result.AshaID,
        "pairing_code": result.PairingCode,
        "device": added_device
    } # noqa


@router.post("/claim_device")
async def claim_device_route(
    payload: ClaimDeviceRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    user = await User.get(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    slogger.info(f"User {user.Email} claiming pairing code: {payload.pairing_code}") # noqa
    res = await validate_and_commission_project(payload.pairing_code, owner_email=user.Email) # noqa
    return res


@router.get("/my_devices")
async def get_my_devices_route(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub")
    user = await User.get(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    slogger.info(f"Fetching devices for user: {user.Email}")
    projects = await get_user_projects(user.Email)
    return projects


@router.post("/user_uncommission_device")
async def user_uncommission_device_route(
    payload: UncommissionRequest,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user.get("sub")
    user = await User.get(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")

    slogger.info(f"User {user.Email} uncommissioning pairing code: {payload.pairing_code}") # noqa
    res = await uncommission_project(payload.pairing_code, owner_email=user.Email) # noqa
    return res
