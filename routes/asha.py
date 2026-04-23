# this file is for the hardware - software communication only!


from fastapi import APIRouter, HTTPException
from schema.asha import AshaVerificationRequest
from repository.asha_repo import check_ashaID_exists


router = APIRouter(prefix="/api/v1/asha", tags=["asha"])


@router.get("/verify_and_register_device")
async def verify_device(ashaID: AshaVerificationRequest):
    is_valid = await check_ashaID_exists(ashaID.auth_id)
    if not is_valid:
        return HTTPException(status_code=404, detail="ASHA ID not found.")
    return HTTPException(status_code=200, detail="ASHA ID is valid.")
