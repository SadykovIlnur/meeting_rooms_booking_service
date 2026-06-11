from pydantic import BaseModel


class RoomResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
