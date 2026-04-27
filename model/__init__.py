from model.user import User
from model.project import Project
from model.asha_device import AshaDevice

__all__ = ["User", "Project"]

document_models = [
    User,
    Project,
    AshaDevice
]
