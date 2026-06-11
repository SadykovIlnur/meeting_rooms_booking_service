from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class UserCreate(UserBase):
    password: str
