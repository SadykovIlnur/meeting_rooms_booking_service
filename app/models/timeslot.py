from datetime import time
from typing import List

from sqlalchemy import Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.booking import Booking


class Timeslot(Base):
    __tablename__ = "timeslots"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    bookings: Mapped[List["Booking"]] = relationship(back_populates="timeslot")

    def __repr__(self) -> str:
        return (
            f"Timeslot(id={self.id}, "
            f"start={self.start_time}, end={self.end_time})"
        )
