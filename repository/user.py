from model.user import User
from schema.user import UserCreate
from fastapi import HTTPException
from utils.hasher import hashPwd


async def user_exists(email: str) -> bool:
    return await User.find_one(User.Email == email) is not None


async def create_an_asha_user(user: UserCreate):
    user_exists_already = await user_exists(user.Email)
    if user_exists_already:
        raise HTTPException(status_code=400, detail="User with this email already exists.")# noqa
    new_user = User(**user.model_dump())
    new_user.Password = hashPwd(new_user.Password)
    await new_user.insert()
    return new_user


async def get_hashed_password(email: str) -> str | None:
    user = await User.find_one(User.Email == email)
    if user:
        return user.Password
    return None


async def get_user_by_email(email: str) -> User | None:
    return await User.find_one(User.Email == email)
