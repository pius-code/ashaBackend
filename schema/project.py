from pydantic import BaseModel


class projectCreate(BaseModel):
    Name: str | None = None
