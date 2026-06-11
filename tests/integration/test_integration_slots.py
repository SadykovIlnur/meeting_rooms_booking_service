import pytest
from fastapi import status
from httpx import AsyncClient

from app import constants


@pytest.mark.asyncio
async def test_get_slots(async_client: AsyncClient, employee_token: str):
    """Успешное получение списка временных слотов."""
    response = await async_client.get(
        "/slots", headers={"Authorization": f"Bearer {employee_token}"}
    )
    data = response.json()
    times = {(slot["start_time"], slot["end_time"]) for slot in data}
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == constants.COUNT_SLOTS_INT_TEST
    for slot in data:
        assert "id" in slot
        assert "start_time" in slot
        assert "end_time" in slot
    assert constants.EXPECTED_TIME_PAIRS.issubset(times)


@pytest.mark.asyncio
async def test_get_slots_without_token(async_client: AsyncClient):
    """Провальный запрос без токена."""
    response = await async_client.get("/slots")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Недействительный токен"
