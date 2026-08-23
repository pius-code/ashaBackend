from model.project import Project
from model.asha_device import AshaDevice
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
        Status="uncommissioned",
        Owner_Email=None
    )

    await new_project.insert()
    return new_project


async def get_all_asha_projects():
    all_projects = await Project.find_all().to_list()
    return all_projects


async def validate_and_commission_project(pairing_code: str, owner_email: str | None = None): # noqa
    code = pairing_code.strip()
    project = await Project.find_one(Project.PairingCode == code)
    if not project:
        # Fallback check on AshaDevice collection for legacy records
        device = await AshaDevice.find_one(AshaDevice.pairing_code == code)
        if device:
            project = await Project.find_one(Project.AshaID == device.asha_id) if device.asha_id else None # noqa
            if not project:
                project = Project(
                    Name="ASHA Device",
                    AshaID=device.asha_id or f"asha_{code}",
                    MacAddress=device.auth_id,
                    PairingCode=code,
                    Status="uncommissioned",
                    Owner_Email=None
                )
                await project.insert()

    if not project:
        return {"valid": False, "detail": "Invalid pairing code"}

    if project.Status == "commissioned":
        return {
            "valid": False,
            "detail": "Device is already commissioned and paired to another account." # noqa
        }

    project.Status = "commissioned"
    if owner_email:
        project.Owner_Email = owner_email
    await project.save()
    return {
        "valid": True,
        "asha_id": project.AshaID,
        "project_name": project.Name,
        "pairing_code": project.PairingCode,
        "status": project.Status,
        "owner_email": project.Owner_Email
    }


async def get_user_projects(owner_email: str):
    projects = await Project.find(Project.Owner_Email == owner_email).to_list()
    results = []
    for proj in projects:
        device_doc = await AshaDevice.find_one(AshaDevice.asha_id == proj.AshaID) # noqa
        if not device_doc and proj.MacAddress:
            device_doc = await AshaDevice.find_one(AshaDevice.auth_id == proj.MacAddress) # noqa
        if not device_doc and proj.PairingCode:
            device_doc = await AshaDevice.find_one(AshaDevice.pairing_code == proj.PairingCode) # noqa

        devices_list = device_doc.devices if device_doc and device_doc.devices else [] # noqa

        formatted_devices = []
        for dev in devices_list:
            if hasattr(dev, "model_dump"):
                formatted_devices.append(dev.model_dump())
            elif hasattr(dev, "dict"):
                formatted_devices.append(dev.dict())
            elif isinstance(dev, dict):
                formatted_devices.append(dev)

        results.append({
            "project_name": proj.Name or "Unnamed Device", # noqa
            "Name": proj.Name or "Unnamed Device", # noqa
            "asha_id": proj.AshaID,
            "AshaID": proj.AshaID,
            "MacAddress": proj.MacAddress or (device_doc.auth_id if device_doc else "N/A"), # noqa
            "PairingCode": proj.PairingCode,
            "Status": proj.Status,
            "Owner_Email": proj.Owner_Email,
            "devices": formatted_devices
        })
    return results


async def uncommission_project(pairing_code: str, owner_email: str | None = None): # noqa
    code = pairing_code.strip()
    project = await Project.find_one(Project.PairingCode == code)
    if not project:
        return {"success": False, "detail": "Project not found for this pairing code"} # noqa

    if owner_email and project.Owner_Email and project.Owner_Email != owner_email: # noqa
        return {"success": False, "detail": "You do not own this device."}

    project.Status = "uncommissioned"
    project.Owner_Email = None
    await project.save()
    return {
        "success": True,
        "message": "Device uncommissioned successfully",
        "pairing_code": project.PairingCode,
        "status": project.Status
    }
