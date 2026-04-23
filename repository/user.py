from model.user import User
from schema.user import UserCreate
from fastapi import HTTPException
from utils.hasher import hashPwd
from utils.asha_utils import gen_ashaID


async def user_exists(email: str) -> bool:
    return await User.find_one(User.Email == email) is not None


async def create_an_asha_user(user: UserCreate):
    user_exists_already = await user_exists(user.Email)
    if user_exists_already:
        raise HTTPException(status_code=400, detail="User with this email already exists.")# noqa
    new_user = User(**user.model_dump())
    new_user.AshaID = await gen_ashaID()
    new_user.Password = hashPwd(new_user.Password)
    await new_user.insert()
    return new_user
