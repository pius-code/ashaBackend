from beanie import Document, Indexed
from typing import Annotated


class Project(Document):
    Name: str | None = None
    AshaID: Annotated[str, Indexed(unique=True)]
    MacAddress: Annotated[str, Indexed(unique=True)] | None = None
    PairingCode: str | None = None
    Status: str = "uncommissioned"  # "uncommissioned" or "commissioned"
    Owner_Email: str | None = None

    class settings:
        name = "Project"
