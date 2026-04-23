from fastapi import APIRouter, HTTPException
from schema.user import UserCreate, UserOut
from repository.user import create_an_asha_user
from utils.logger import slogger

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/create", response_model=UserOut)
async def create_user(user: UserCreate):
    try:
        new_user = await create_an_asha_user(user)
        slogger.info(f"User created successfully: {new_user.Email}")
        return new_user
    except HTTPException as e:
        slogger.error(f"Error creating user: {e.detail}")
        raise e
    except Exception as e:
        slogger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
