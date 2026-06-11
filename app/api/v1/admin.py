from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_admin
from app.db.database import get_db_session
from app.models.booking import Booking
from app.models.user import User
from app.schemas.booking import BookingAdminResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/bookings", response_model=list[BookingAdminResponse])
async def get_all_bookings(
    user_id: int | None = Query(None, description="Фильтрация по user ID"),
    room_id: int | None = Query(None, description="Фильтрация по room ID"),
    booking_date: date | None = Query(
        None, description="Фильтрация по date YYYY-MM-DD"
    ),
    hide_past: bool = Query(
        False, description="Скрыть записи на прошедшие даты"
    ),
    admin: Annotated[User, Depends(get_admin)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[BookingAdminResponse]:
    """Получает все записи от лица админа."""
    query = select(Booking).options(
        selectinload(Booking.room),
        selectinload(Booking.timeslot),
        selectinload(Booking.user),
    )
    if user_id:
        query = query.where(Booking.user_id == user_id)
    if room_id:
        query = query.where(Booking.room_id == room_id)
    if booking_date:
        query = query.where(Booking.booking_date == booking_date)
    if hide_past:
        query = query.where(Booking.booking_date >= date.today())
    result = await db.execute(query.order_by(Booking.booking_date))
    return result.scalars().all()
