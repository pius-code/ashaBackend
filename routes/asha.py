# this file is for the hardware - software communication only!


from fastapi import APIRouter, Depends, HTTPException
from schema.asha import AshaVerificationRequest
from repository.asha_repo import check_ashaID_exists, add_IoT_device, get_all_asha_devices_by_logged_in_user, get_asha_user_projects_and_devices # noqa
from utils.logger import slogger
from middleware.auth import get_current_user


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])


@router.post("/verify_and_register_device")
async def verify_device(AshaIoTPayload: AshaVerificationRequest):
    slogger.info("New device being registered")
    print(AshaIoTPayload)
    is_valid = await check_ashaID_exists(AshaIoTPayload.auth_id)
    if not is_valid:
        raise HTTPException(status_code=404, detail="ASHA ID not found.")
    added_device = await add_IoT_device(AshaIoTPayload)
    return {
        "message": "ASHA ID is valid and device registered successfully.",
        "device": added_device
    } # noqa


@router.post("/get_devices_for_project_by_ashaID")
async def get_devices_for_project(project_id: str):
    pass


@router.post("/get_all_devices_for_project_by_logged_in_user")
async def get_all_devices_for_project_by_logged_in_user(current_user: dict = Depends(get_current_user)): # noqa
    return await get_all_asha_devices_by_logged_in_user(current_user)


@router.post("/get_project_and_devices")
async def get_project_and_devices(current_user: dict = Depends(get_current_user)):
    return await get_asha_user_projects_and_devices(current_user)
