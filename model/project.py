from beanie import Document, Indexed
from typing import Annotated


# asha ID is same as auth_id, the name changed later on
class Project(Document):
    Name: str | None = None
    AshaID: Annotated[str, Indexed(unique=True)]
    Created_by: str | None = None
