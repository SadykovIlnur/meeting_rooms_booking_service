
import asyncio
from datetime import date, time, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.constants import BASE_URL
from app.core.security import hash_password
from app.db.database import get_db_session
from app.main import app
from app.models.base import Base
from app.models.booking import Booking
from app.models.room import Room
from app.models.timeslot import Timeslot
from app.models.user import User


async def seed_db(session: AsyncSession):
    """Заполняет БД тестовыми данными."""
    rooms = [Room(name="Комната 1"), Room(name="Комната 2")]
    slots = [
        Timeslot(start_time=time(9, 0), end_time=time(11, 0)),
        Timeslot(start_time=time(11, 0), end_time=time(13, 0))
    ]
    users = [
        User(
            username="employee1",
            password=hash_password("employee123"),
            role="employee"
        ),
        User(
            username="admin",
            password=hash_password("admin123"),
            role="admin"
        ),
    ]
    session.add_all(rooms)
    session.add_all(slots)
    session.add_all(users)
    await session.commit()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает тестовую сеесию БД с in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool
    )

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        TestingSessionLocal = async_sessionmaker(
            bind=conn,
            expire_on_commit=False
        )
        async with TestingSessionLocal() as session:
            await seed_db(session)
            yield session
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Предоставляет HTTP-клиент для тестирования приложения."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт цикл событий для сессии тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


async def get_token(client: AsyncClient, username: str, password: str) -> str:
    """Получает токен пользователя."""
    response = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def employee_token(client: AsyncClient) -> str:
    """Токен сотрудника."""
    return await get_token(client, "employee1", "employee123")


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Токен админа."""
    return await get_token(client, "admin", "admin123")


@pytest.fixture
def booking_date() -> str:
    """Дата бронирования (завтра) в ISO-формате."""
    return (date.today() + timedelta(days=1)).isoformat()


async def post_booking(
    client: AsyncClient,
    token: str,
    room_id: int = 1,
    timeslot_id: int = 1,
) -> Response:
    """Создаёт запрос на бронирование с заданными параметрами."""
    booking_date = (date.today() + timedelta(days=1)).isoformat()
    return await client.post(
        "/bookings",
        json={
            "room_id": room_id,
            "timeslot_id": timeslot_id,
            "booking_date": booking_date
        },
        headers={"Authorization": f"Bearer {token}"}
    )


@pytest_asyncio.fixture
async def create_booking_base(db_session: AsyncSession):
    """Фабрика для создания бронирования с произвольным сдвигом даты."""
    async def _create(
        user_id: int = 1,
        room_id: int = 1,
        timeslot_id: int = 1,
        days_delta: int = 1,
    ):
        booking_date = date.today() + timedelta(days=days_delta)
        booking = Booking(
            user_id=user_id,
            room_id=room_id,
            timeslot_id=timeslot_id,
            booking_date=booking_date,
        )
        db_session.add(booking)
        await db_session.commit()
        await db_session.refresh(booking)
        return booking
    return _create


@pytest_asyncio.fixture
async def create_booking(create_booking_base):
    """Создаёт бронирование на будущую дату (+1 день)."""
    async def _create(user_id: int = 1, room_id: int = 1, timeslot_id: int = 1):
        return await create_booking_base(
            user_id=user_id,
            room_id=room_id,
            timeslot_id=timeslot_id,
            days_delta=1
        )
    return _create


@pytest_asyncio.fixture
async def create_past_booking(create_booking_base):
    """Создаёт бронирование на прошедшую дату (-1 день)."""
    async def _create(user_id: int = 1, room_id: int = 1, timeslot_id: int = 1):
        return await create_booking_base(
            user_id=user_id,
            room_id=room_id,
            timeslot_id=timeslot_id,
            days_delta=-1
        )
    return _create
