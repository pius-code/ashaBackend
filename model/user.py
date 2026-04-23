from beanie import Document, Indexed
from typing import Annotated


class User(Document):
    Email: Annotated[str, Indexed(unique=True)]
    Name: str
    Password: str

    class Settings:
        name = "users"
