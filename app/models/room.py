from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import MAX_ROOMNAME_LENGTH
from app.models.base import Base
from app.models.booking import Booking


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(MAX_ROOMNAME_LENGTH), unique=True, nullable=False
    )

    bookings: Mapped[List["Booking"]] = relationship(back_populates="room")

    def __repr__(self) -> str:
        return f"Room(id={self.id}, name='{self.name}'"
