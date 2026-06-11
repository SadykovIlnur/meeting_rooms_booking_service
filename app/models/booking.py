from datetime import date

from sqlalchemy import Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    timeslot_id: Mapped[int] = mapped_column(
        ForeignKey("timeslots.id", ondelete="CASCADE"), nullable=False
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)

    user: Mapped["User"] = relationship(back_populates="bookings")
    room: Mapped["Room"] = relationship(back_populates="bookings")
    timeslot: Mapped["Timeslot"] = relationship(back_populates="bookings")

    __table_args__ = (
        UniqueConstraint(
            "room_id", "timeslot_id", "booking_date", name="unique_booking"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Booking(id={self.id}, user_id={self.user_id}, "
            f"room_id={self.room_id}, time_slot_id={self.timeslot_id}, "
            f"booking_date={self.booking_date})>"
        )
