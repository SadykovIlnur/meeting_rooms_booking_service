import pytest
from fastapi import status
from httpx import AsyncClient

from app.constants import COUNT_SLOTS_UNIT_TEST


@pytest.mark.asyncio
async def test_get_slots(client: AsyncClient, employee_token: str):
    """Успешное получение списка временных слотов."""
    response = await client.get(
        "/slots", headers={"Authorization": f"Bearer {employee_token}"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == COUNT_SLOTS_UNIT_TEST
    for slot in data:
        assert "id" in slot
        assert "start_time" in slot
        assert "end_time" in slot


@pytest.mark.asyncio
async def test_get_slots_without_token(client: AsyncClient):
    """Провальный запрос без токена."""
    response = await client.get("/slots")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"
