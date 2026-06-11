from datetime import date

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo

from app.schemas.room import RoomResponse
from app.schemas.timeslot import SlotResponse
from app.schemas.user import UserBase


class BookingBase(BaseModel):
    room_id: int
    timeslot_id: int
    booking_date: date


class BookingCreate(BookingBase):

    @field_validator("booking_date")
    @classmethod
    def date_not_in_past(cls, date_field: date, info: ValidationInfo) -> date:
        if date_field < date.today():
            raise ValueError("Указана неверная дата.")
        return date_field


class BookingCreateResponse(BookingBase):
    id: int


class BookingResponse(BaseModel):
    id: int
    booking_date: date
    room: RoomResponse
    timeslot: SlotResponse

    model_config = {"from_attributes": True}


class BookingAdminResponse(BookingResponse):
    user: UserBase | None = None
