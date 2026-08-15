# this file is for the hardware - software communication only!


from fastapi import APIRouter
from schema.project import projectCreate
from schema.asha import AshaVerificationRequest, ashaDeviceSchema, PairingCodeCheckRequest, UncommissionRequest # noqa
from repository.asha_repo import add_IoT_device
from utils.logger import slogger
from repository.projects import create_an_asha_project, validate_and_commission_project, uncommission_project # noqa


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


@router.post("/is_pairing_code_valid")
async def check_pairing_code_valid(payload: PairingCodeCheckRequest):
    slogger.info(f"Validating pairing code: {payload.pairing_code}")
    res = await validate_and_commission_project(payload.pairing_code)
    return res


@router.post("/uncommission_device")
async def uncommission_device_route(payload: UncommissionRequest):
    slogger.info(f"Uncommissioning device with code: {payload.pairing_code}")
    res = await uncommission_project(payload.pairing_code)
    return res


# @router.post("/get_devices_for_project_by_ashaID")
# async def get_devices_for_project(project_id: str):
#     pass


# @router.post("/get_all_devices_for_project_by_logged_in_user")
# async def get_all_devices_for_project_by_logged_in_user(current_user: dict = Depends(get_current_user)): # noqa
#     return await get_all_asha_devices_by_logged_in_user(current_user)


# @router.post("/get_project_and_devices")
# async def get_project_and_devices(current_user: dict = Depends(get_current_user)): # noqa
#     return await get_asha_user_projects_and_devices(current_user)
