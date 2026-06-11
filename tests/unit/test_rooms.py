import pytest
from fastapi import status
from httpx import AsyncClient

from app.constants import COUNT_ROOMS_UNIT_TEST
from tests.unit.conftest import post_booking


@pytest.mark.asyncio
async def test_get_rooms(client: AsyncClient, employee_token: str):
    """Успешное получение списка комнат."""
    response = await client.get(
        "/rooms",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == COUNT_ROOMS_UNIT_TEST
    for room in data:
        assert "id" in room
        assert "name" in room


@pytest.mark.asyncio
async def test_get_rooms_without_token(client: AsyncClient):
    """Провальный запрос получения списка комнат без токена."""
    response = await client.get("/rooms")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"


@pytest.mark.asyncio
async def test_get_availability(
    client: AsyncClient, employee_token: str, booking_date: str
):
    """Успешное получение доступности на корректную дату."""
    response = await client.get(
        f"/rooms/availability?date_str={booking_date}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    for room in data:
        assert "room_id" in room
        assert "room_name" in room
        assert "slots" in room
        for slot in room["slots"]:
            assert "slot_id" in slot
            assert "start_time" in slot
            assert "end_time" in slot
            assert "is_booked" in slot
            assert slot["is_booked"] is False


@pytest.mark.asyncio
async def test_get_availability_with_booking(
    client: AsyncClient, employee_token: str, booking_date: str
):
    """После создания бронирования слот помечается is_booked=true."""
    await post_booking(client, employee_token, room_id=1, timeslot_id=1)
    response = await client.get(
        f"/rooms/availability?date_str={booking_date}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    data = response.json()
    room = next(room for room in data if room["room_id"] == 1)
    slot = next(slot for slot in room["slots"] if slot["slot_id"] == 1)
    assert slot["is_booked"] is True


@pytest.mark.asyncio
async def test_get_availability_with_invalid_date(
    client: AsyncClient, employee_token: str
):
    """Запрос с неправильным форматом даты."""
    response = await client.get(
        "/rooms/availability?date_str=2023-12-40",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Неправильный формат даты: YYYY-MM-DD"


@pytest.mark.asyncio
async def test_get_availability_without_token(
    client: AsyncClient, booking_date: str
):
    """Провальный запрос без токена."""
    response = await client.get(f"/rooms/availability?date_str={booking_date}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"
