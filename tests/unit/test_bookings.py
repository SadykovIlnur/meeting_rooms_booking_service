from datetime import date, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from app import constants
from tests.unit.conftest import post_booking


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient, employee_token: str, booking_date: str,
):
    """Успешное создание записи."""
    response = await post_booking(client, employee_token)
    data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert data["room_id"] == constants.ROOM_ID_UNIT_TEST
    assert data["timeslot_id"] == constants.TIMESLOT_ID_UNIT_TEST
    assert data["booking_date"] == booking_date


@pytest.mark.asyncio
async def test_create_booking_conflict(
    client: AsyncClient, employee_token: str
):
    """Нельзя создать запись на существующий временной слот."""
    await post_booking(client, employee_token)
    response = await post_booking(client, employee_token)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Временной слот уже занят"


@pytest.mark.asyncio
async def test_create_booking_not_exist_room(
    client: AsyncClient, employee_token: str, booking_date: str
):
    """Нельзя создать запись на несуществующую комнату."""
    response = await client.post(
        "/bookings",
        json={
            "room_id": 10,
            "timeslot_id": 1,
            "booking_date": booking_date
        },
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Такой комнаты не существует"


@pytest.mark.asyncio
async def test_create_booking_not_exist_timeslot(
    client: AsyncClient, employee_token: str, booking_date: str
):
    """Нельзя создать запись на несуществующий временной слот."""
    response = await client.post(
        "/bookings",
        json={
            "room_id": 1,
            "timeslot_id": 10,
            "booking_date": booking_date
        },
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Такого временного слота не существует"


@pytest.mark.asyncio
async def test_create_booking_past_date(
    client: AsyncClient, employee_token: str
):
    """Нельзя создать запись на прошедшую дату."""
    booking_date = (date.today() - timedelta(days=1)).isoformat()
    response = await client.post(
        "/bookings",
        json={
            "room_id": 1,
            "timeslot_id": 1,
            "booking_date": booking_date
        },
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    detail = response.json()["detail"]
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any("Указана неверная дата" in str(err) for err in detail)


@pytest.mark.asyncio
async def test_create_booking_without_token(
    client: AsyncClient, booking_date: str
):
    """Нельзя создать запись без токена."""
    response = await client.post(
        "/bookings",
        json={"room_id": 1, "timeslot_id": 1, "booking_date": booking_date}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"


@pytest.mark.asyncio
async def test_delete_own_booking(client: AsyncClient, employee_token: str):
    """Успешное удаление своей записи."""
    create_response = await post_booking(client, employee_token)
    booking_id = create_response.json()["id"]
    delete_response = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_others_booking_as_employee(
    client: AsyncClient, admin_token: str, employee_token: str
):
    """Нельзя удалить чужую запись."""
    response_employee1 = await post_booking(client, admin_token)
    booking_id = response_employee1.json()["id"]
    response_employee2 = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response_employee2.status_code == status.HTTP_403_FORBIDDEN
    assert response_employee2.json()["detail"] == "Данную бронь отменить нельзя"


@pytest.mark.asyncio
async def test_delete_booking_not_exist(
    client: AsyncClient, employee_token: str
):
    """Нельзя удалить несуществующую запись."""
    response = await client.delete(
        "/bookings/10",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Такой брони не существует"


@pytest.mark.asyncio
async def test_delete_booking_past_date(
    client: AsyncClient, employee_token: str, create_past_booking
):
    """Нельзя удалить запись на прошедшую дату."""
    booking = await create_past_booking()
    response = await client.delete(
        f"/bookings/{booking.id}",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Данную бронь отменить нельзя"


@pytest.mark.asyncio
async def test_delete_booking_without_token(
    client: AsyncClient, employee_token: str
):
    """Нельзя удалить запись без токена."""
    response_create = await post_booking(client, employee_token)
    booking_id = response_create.json()["id"]
    response = await client.delete(f"/bookings/{booking_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"


@pytest.mark.asyncio
async def test_delete_others_booking_as_admin(
    client: AsyncClient, admin_token: str, employee_token: str
):
    """Успешное удаление админом чужой записи."""
    create_response = await post_booking(client, employee_token)
    booking_id = create_response.json()["id"]
    response = await client.delete(
        f"/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_get_my_bookings(
    client: AsyncClient, employee_token: str, admin_token: str
):
    """Успешное получение своих записей."""
    await post_booking(client, employee_token)
    await post_booking(client, admin_token, room_id=2, timeslot_id=2)
    response = await client.get(
        "/bookings/my",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == constants.COUNT_BOOKINGS_UNIT_TEST


@pytest.mark.asyncio
async def test_get_my_bookings_without_token(client: AsyncClient):
    """Провальный запрос без токена."""
    response = await client.get("/bookings/my")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"
