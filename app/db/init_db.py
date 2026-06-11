import asyncio
import csv
from datetime import time
from pathlib import Path
from typing import Callable, Dict, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import DATA_DIR
from app.core.security import hash_password
from app.db.database import db_dependency
from app.models.room import Room
from app.models.timeslot import Timeslot
from app.models.user import User


TableModel = TypeVar("TableModel")


def parse_time(time_str: str) -> time:
    """Преобразует время из str в time."""
    hours, minutes = map(int, time_str.split(':'))
    return time(hours, minutes)


async def load_from_csv(
    session: AsyncSession,
    model: Type[TableModel],
    csv_path: Path,
    row_builder: Callable[[Dict[str, str]], TableModel],
) -> None:

    result = await session.execute(select(model).limit(1))
    if result.scalars().first() is not None:
        return

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        objects = [row_builder(row) for row in reader]

    session.add_all(objects)
    await session.commit()


async def load_rooms_from_csv(session: AsyncSession, csv_path: Path) -> None:
    """Заполняет таблицу Room БД."""

    await load_from_csv(
        session,
        Room,
        csv_path,
        lambda row: Room(name=row["name"])
    )


async def load_timeslots_from_csv(
        session: AsyncSession, csv_path: Path
) -> None:
    """Заполняет таблицу Timeslot БД."""

    await load_from_csv(
        session,
        Timeslot,
        csv_path,
        lambda row: Timeslot(
            start_time=parse_time(row["start_time"]),
            end_time=parse_time(row["end_time"])
        )
    )


async def load_users_from_csv(session: AsyncSession, csv_path: Path) -> None:
    """Заполняет таблицу User БД."""
    await load_from_csv(
        session,
        User,
        csv_path,
        lambda row: User(
            username=row["username"],
            password=hash_password(row["password"]),
            role=row["role"]
        )
    )


async def init_data() -> None:
    async with db_dependency.session_factory() as session:
        await load_rooms_from_csv(session, DATA_DIR / "rooms.csv")
        await load_timeslots_from_csv(session, DATA_DIR / "timeslots.csv")
        await load_users_from_csv(session, DATA_DIR / "users.csv")


def main():
    asyncio.run(init_data())


if __name__ == "__main__":
    main()
