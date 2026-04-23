from model.project import Project
from utils.asha_utils import gen_ashaID


async def create_an_asha_project(projectCreate):
    new_project = Project(**projectCreate.model_dump())
    new_project.ashaID = await gen_ashaID()
    await new_project.insert()

    return f"created a new project with name {new_project.name}"
