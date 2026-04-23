from fastapi import APIRouter, HTTPException
from schema.user import UserCreate, UserOut, UserLogIn
from repository.user import create_an_asha_user, get_hashed_password, get_user_by_email # noqa
from utils.logger import slogger
from utils.hasher import verifyPwd
from helpers.auth import generate_token

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


@router.post("/login")
async def login_admin(payload: UserLogIn):
    """Login and return JWT token"""
    hashed_password = await get_hashed_password(payload.Email)
    user = await get_user_by_email(payload.Email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials or user not found") # noqa
    if not verifyPwd(payload.Password, str(hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id),
    }
