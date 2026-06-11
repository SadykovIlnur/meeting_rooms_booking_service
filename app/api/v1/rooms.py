from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db_session
from app.models.booking import Booking
from app.models.room import Room
from app.models.timeslot import Timeslot
from app.models.user import User
from app.schemas.room import RoomResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=list[RoomResponse])
async def get_rooms(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[RoomResponse]:
    """Возвращает все возможные комнаты."""
    result = await db.execute(select(Room))
    rooms = result.scalars().all()
    return rooms


@router.get("/availability")
async def get_availability(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    date_str: str = Query(..., description="YYYY-MM-DD"),
):
    """Показывает доступность записей на конкретную дату."""
    try:
        booking_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неправильный формат даты: YYYY-MM-DD"
        )

    rooms_result = await db.execute(select(Room))
    rooms = rooms_result.scalars().all()
    slots_result = await db.execute(select(Timeslot))
    slots = slots_result.scalars().all()
    bookings_result = await db.execute(
        select(Booking).where(Booking.booking_date == booking_date)
    )
    bookings = bookings_result.scalars().all()
    booked_set = {
        (booking.room_id, booking.timeslot_id) for booking in bookings
    }

    availability = []
    for room in rooms:
        slots_availability = []
        for slot in slots:
            is_booked = (room.id, slot.id) in booked_set
            slots_availability.append(
                {
                    "slot_id": slot.id,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "is_booked": is_booked,
                }
            )
        availability.append(
            {
                "room_id": room.id,
                "room_name": room.name,
                "slots": slots_availability,
            }
        )
    return availability
