from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db_session
from app.models.timeslot import Timeslot
from app.models.user import User
from app.schemas.timeslot import SlotResponse

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.get("", response_model=list[SlotResponse])
async def get_slots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SlotResponse]:
    """Возвращает все возможные слоты."""
    result = await db.execute(select(Timeslot))
    slots = result.scalars().all()
    return slots
