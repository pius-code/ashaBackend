from uuid import uuid4
from repository.asha_repo import check_ashaID_exists
import uuid 


async def gen_ashaID() -> str:
    new_id = str(uuid4())
    while await check_ashaID_exists(new_id):
        new_id = str(uuid4())
    return new_id


def gen_correlation_id() -> str:
    return str(uuid.uuid4())
