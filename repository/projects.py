from model.project import Project
from utils.asha_utils import gen_ashaID
from schema.project import projectCreate


async def create_an_asha_project(projectdet: projectCreate):
    generated_id = await gen_ashaID()
    new_project = Project(
        Name=projectdet.Name,
        AshaID=generated_id,
    )

    await new_project.insert()
    return f"created a new project with name {new_project.Name}"
