from beanie import Document, Indexed
from typing import Annotated


class Project(Document):
    name: str | None = None
    ashaID: Annotated[str, Indexed(unique=True)]
    created_by: str | None = None
