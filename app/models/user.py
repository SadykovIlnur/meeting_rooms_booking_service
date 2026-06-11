import enum
from typing import List

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import MAX_LENGTH_PASSWORD, MAX_USERNAME_LENGTH
from app.models.base import Base
from app.models.booking import Booking


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(MAX_USERNAME_LENGTH), unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(
        String(MAX_LENGTH_PASSWORD), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE
    )

    bookings: Mapped[List["Booking"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"role='{self.role}')"
        )
