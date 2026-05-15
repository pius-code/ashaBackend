from model.project import Project
from model.asha_device import AshaDevice
from schema.asha import AshaVerificationRequest
from beanie.operators import In


async def check_ashaID_exists(asha_id: str) -> bool:
    return await Project.find_one(Project.AshaID == asha_id) is not None


async def add_IoT_device(AshaIoTPayload: AshaVerificationRequest):
    existing_registry = await AshaDevice.find_one(
        AshaDevice.auth_id == AshaIoTPayload.auth_id
    )

    if existing_registry:
        existing_registry.devices = AshaIoTPayload.devices
        await existing_registry.save()
        return existing_registry
    else:
        new_device = AshaDevice(**AshaIoTPayload.model_dump())
        await new_device.insert()
        return new_device


async def get_all_asha_devices_by_logged_in_user(current_user: dict): # noqa
    user_projects = await Project.find(Project.Created_by == current_user["sub"]).to_list() # noqa
    user_asha_ids = [project.AshaID for project in user_projects]
    if not user_asha_ids:
        return []
    devices = await AshaDevice.find(
        In("auth_id", user_asha_ids)
    ).to_list()
    return devices


async def get_asha_user_projects_and_devices(current_user: dict):
    user_projects = await Project.find(
        Project.Created_by == current_user["sub"]
    ).to_list()
    result = []
    for project in user_projects:
        registry = await AshaDevice.find_one(
            AshaDevice.auth_id == project.AshaID
        )
        project_devices = registry.devices if registry else [] # noqa   
        result.append({
            "project_name": project.Name,
            "asha_id": project.AshaID,
            "devices": [
                {
                    "device_id": d.device_id,
                    "metadata": d.metadata,
                    "category": d.category,
                    "bus": d.bus,
                    "pin": d.pin
                }
                for d in project_devices
            ]
        })
    return result
