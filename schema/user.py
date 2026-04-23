from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    Email: EmailStr
    Name: str
    Password: str


class UserOut(BaseModel):
    Email: EmailStr
    Name: str
    AshaID: str = None


class UserLogIn(BaseModel):
    Email: EmailStr
    Password: str
