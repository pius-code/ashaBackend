from beanie import Document, Indexed
from typing import Annotated


class User(Document):
    Email: Annotated[str, Indexed(unique=True)]
    Name: str
    Password: str
    AshaID: str | None = None

    class Collection:
        name = "users"
