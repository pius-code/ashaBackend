from model.project import Project


async def check_ashaID_exists(asha_id: str) -> bool:
    return await Project.find_one(Project.AshaID == asha_id) is not None
