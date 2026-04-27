from model.project import Project
from utils.asha_utils import gen_ashaID
from schema.project import projectCreate


async def create_an_asha_project(projectdet: projectCreate, current_user: dict): # noqa
    generated_id = await gen_ashaID()
    new_project = Project(
        Name=projectdet.Name,
        AshaID=generated_id,
        Created_by=current_user["sub"]
    )

    await new_project.insert()
    return f"created a new project with name {new_project}"


async def get_all_asha_projects():
    all_projects = await Project.find_all().to_list()
    return all_projects
