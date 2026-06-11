from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.db.database import get_db_session
from app.models.booking import Booking
from app.models.room import Room
from app.models.timeslot import Timeslot
from app.models.user import User
from app.schemas.booking import (
    BookingBase,
    BookingCreate,
    BookingCreateResponse,
    BookingResponse,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "",
    response_model=BookingCreateResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_booking(
    booking_data: BookingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookingBase:
    """Создает запись."""
    room = await db.get(Room, booking_data.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой комнаты не существует"
        )

    slot = await db.get(Timeslot, booking_data.timeslot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такого временного слота не существует"
        )

    existing_booking = await db.execute(
        select(Booking).where(
            Booking.room_id == booking_data.room_id,
            Booking.timeslot_id == booking_data.timeslot_id,
            Booking.booking_date == booking_data.booking_date,
        )
    )
    if existing_booking.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Временной слот уже занят"
        )

    new_booking = Booking(
        user_id=current_user.id,
        room_id=booking_data.room_id,
        timeslot_id=booking_data.timeslot_id,
        booking_date=booking_data.booking_date,
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    return new_booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Удаляет запись."""
    booking = await db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Такой брони не существует"
        )

    if current_user.role != "admin" and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Данную бронь отменить нельзя"
        )

    if booking.booking_date <= date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Данную бронь отменить нельзя"
        )

    await db.delete(booking)
    await db.commit()


@router.get("/my", response_model=list[BookingResponse])
async def get_my_bookings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[BookingResponse]:
    """Показывает все записи пользователя."""
    today = date.today()
    result = await db.execute(
        select(Booking)
        .where(
            Booking.user_id == current_user.id, Booking.booking_date >= today
        )
        .options(selectinload(Booking.room), selectinload(Booking.timeslot))
        .order_by(Booking.booking_date, Booking.timeslot_id)
    )
    return result.scalars().all()
