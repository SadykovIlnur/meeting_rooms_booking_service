from datetime import date, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient

from app import constants


@pytest.mark.asyncio
async def test_admin_get_all_bookings(
    client: AsyncClient, admin_token: str, create_booking
):
    """Получение всех записей админом."""
    await create_booking()
    response = await client.get(
        "/admin/bookings", headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == constants.COUNT_BOOKINGS_UNIT_TEST


@pytest.mark.asyncio
async def test_admin_filter_by_user(
    client: AsyncClient, admin_token: str, create_booking
):
    """Получение всех записей админом c фильтрацией по пользователю."""
    await create_booking()
    await create_booking(user_id=2, room_id=2, timeslot_id=2)
    response = await client.get(
        "/admin/bookings?user_id=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert all(booking["user"]["id"] == 1 for booking in data)


@pytest.mark.asyncio
async def test_admin_filter_by_room_id(
    client: AsyncClient, admin_token: str, create_booking
):
    """Получение всех записей админом c фильтрацией по room_id."""
    await create_booking()
    await create_booking(user_id=2, room_id=2, timeslot_id=2)
    response = await client.get(
        "/admin/bookings?room_id=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == constants.COUNT_BOOKINGS_UNIT_TEST
    assert data[0]["room"]["id"] == constants.ROOM_ID_UNIT_TEST


@pytest.mark.asyncio
async def test_admin_filter_by_booking_date(
    client: AsyncClient, admin_token: str
):
    """Получение всех записей админом c фильтрацией по booking_date."""
    booking_date1 = date.today() + timedelta(days=1)
    booking_date2 = date.today() + timedelta(days=2)
    await client.post(
        "/bookings",
        json={
            "room_id": 1,
            "timeslot_id": 1,
            "booking_date": booking_date1.isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    await client.post(
        "/bookings",
        json={
            "room_id": 1,
            "timeslot_id": 2,
            "booking_date": booking_date2.isoformat()
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = await client.get(
        f"/admin/bookings?booking_date={booking_date1.isoformat()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == constants.COUNT_BOOKINGS_UNIT_TEST


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoint(
    client: AsyncClient, employee_token: str
):
    """Эндпоинт с префиксом /admin недоступен обычным пользователям."""
    response = await client.get(
        "/admin/bookings",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Недостаточно прав"


@pytest.mark.asyncio
async def test_admin_without_token(client: AsyncClient):
    """Эндпоинт с префиксом /admin недоступен без токена."""
    response = await client.get("/admin/bookings")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"
