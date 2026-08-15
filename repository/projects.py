from model.project import Project
from utils.asha_utils import gen_ashaID
from schema.project import projectCreate


async def create_an_asha_project(projectdet: projectCreate): # noqa
    existing_project = await Project.find_one(Project.MacAddress == projectdet.MacAddress) # noqa
    if existing_project and existing_project.Status == "commissioned":
        if projectdet.Name:
            existing_project.Name = projectdet.Name
            await existing_project.save()
        return existing_project

    generated_id = await gen_ashaID()
    pairing_code = generated_id[0:8]

    if existing_project:
        existing_project.AshaID = generated_id
        existing_project.PairingCode = pairing_code
        await existing_project.save()
        return existing_project

    new_project = Project(
        Name=projectdet.Name,
        AshaID=generated_id,
        PairingCode=pairing_code,
        MacAddress=projectdet.MacAddress,
        Status="uncommissioned"
    )

    await new_project.insert()
    return new_project


async def get_all_asha_projects():
    all_projects = await Project.find_all().to_list()
    return all_projects


async def validate_and_commission_project(pairing_code: str):
    project = await Project.find_one(Project.PairingCode == pairing_code)
    if not project:
        return {"valid": False, "detail": "Invalid pairing code"}

    project.Status = "commissioned"
    await project.save()
    return {
        "valid": True,
        "asha_id": project.AshaID,
        "project_name": project.Name,
        "pairing_code": project.PairingCode,
        "status": project.Status
    }


async def uncommission_project(pairing_code: str):
    project = await Project.find_one(Project.PairingCode == pairing_code)
    if not project:
        return {"success": False, "detail": "Project not found for this pairing code"}

    project.Status = "uncommissioned"
    await project.save()
    return {
        "success": True,
        "message": "Device uncommissioned successfully",
        "pairing_code": project.PairingCode,
        "status": project.Status
    }


# async def get_phone_by_asha_id(asha_id: str) -> str | None:
#     project = await Project.find_one(Project.AshaID == asha_id)
#     return project.PhoneNumber if project else None
