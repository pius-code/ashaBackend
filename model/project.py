from beanie import Document, Indexed
from typing import Annotated


class Project(Document):
    Name: str | None = None
    AshaID: Annotated[str, Indexed(unique=True)]
    Created_by: str | None = None
