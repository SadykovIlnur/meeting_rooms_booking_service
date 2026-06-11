import asyncio
from datetime import date, timedelta
from typing import AsyncGenerator, AsyncIterator
from urllib.parse import urlparse, urlunparse

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from app import constants
from app.db.database import get_db_session
from app.db.init_db import (
    load_rooms_from_csv,
    load_timeslots_from_csv,
    load_users_from_csv,
)
from app.main import app
from app.models.base import Base
from app.models.booking import Booking


@pytest.fixture(scope="session")
def event_loop():
    """Создаёт цикл событий для сессии тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncIterator[PostgresContainer]:
    """Запускает контейнер с тестовой БД."""
    with PostgresContainer(constants.POSTGRES_IMAGE) as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def test_engine(postgres_container: PostgresContainer) -> AsyncEngine:
    """Создаёт асинхронный движок SQLAlchemy для тестовой БД."""
    sync_url = urlparse(postgres_container.get_connection_url())
    async_url = urlunparse(sync_url._replace(scheme="postgresql+asyncpg"))
    engine = create_async_engine(async_url, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def seed_data(test_engine: AsyncEngine):
    """Загружает начальные данные."""
    async with async_sessionmaker(
        test_engine, expire_on_commit=False
    )() as session:
        await load_rooms_from_csv(session, constants.DATA_DIR / "rooms.csv")
        await load_timeslots_from_csv(
            session, constants.DATA_DIR / "timeslots.csv"
        )
        await load_users_from_csv(session, constants.DATA_DIR / "users.csv")


@pytest_asyncio.fixture
async def db_session(
    test_engine: AsyncEngine, seed_data: None
) -> AsyncGenerator[AsyncSession, None]:
    """Сессия с автоматическим откатом транзакции после теста."""
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()


@pytest_asyncio.fixture
async def async_client(
    db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """Создаёт HTTP-клиент для тестирования."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=constants.BASE_URL
    ) as client:
        yield client
    app.dependency_overrides.clear()


async def get_token(client: AsyncClient, username: str, password: str) -> str:
    """Получает токен пользователя."""
    response = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def employee_token(async_client: AsyncClient) -> str:
    """Токен сотрудника."""
    return await get_token(async_client, "employee1", "employee123")


@pytest_asyncio.fixture
async def admin_token(async_client: AsyncClient) -> str:
    """Токен админа."""
    return await get_token(async_client, "admin", "admin123")


@pytest.fixture
def booking_date() -> str:
    """Дата бронирования (завтра) в ISO-формате."""
    return (date.today() + timedelta(days=1)).isoformat()


async def post_booking(
    async_client: AsyncClient,
    token: str,
    room_id: int = 1,
    timeslot_id: int = 1,
) -> Response:
    """Создаёт запрос на бронирование с заданными параметрами."""
    booking_date = (date.today() + timedelta(days=1)).isoformat()
    return await async_client.post(
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
    ) -> Booking:
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
