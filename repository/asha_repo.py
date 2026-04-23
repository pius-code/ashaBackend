from model.user import User


async def check_ashaID_exists(asha_id: str) -> bool:
    return await User.find_one(User.AshaID == asha_id) is not None
