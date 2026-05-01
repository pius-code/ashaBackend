from model.project import Project
from model.asha_device import AshaDevice
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from model import document_models as all_models

_db_initialized = False

async def init_db_if_needed():
    global _db_initialized
    if not _db_initialized:
        load_dotenv()
        mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
        await init_beanie(
            database=mongo_client.get_default_database(),
            document_models=all_models,
        )
        _db_initialized = True

async def get_asha_user_projects_and_devices():
    await init_db_if_needed()
    user_projects = await Project.find(
        Project.Created_by == "69e9de328ab270d2e2416395"
    ).to_list()
    result = []
    for project in user_projects:
        registry = await AshaDevice.find_one(
            AshaDevice.auth_id == project.AshaID
        )
        project_devices = registry.devices if registry else []
        
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
