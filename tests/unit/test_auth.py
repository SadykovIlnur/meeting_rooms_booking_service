import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Успешное логирование и получение токена."""
    response = await client.post(
        "/auth/login",
        json={"username": "employee1", "password": "employee123"}
    )
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Вход с неправильным паролем."""
    response = await client.post(
        "/auth/login",
        json={"username": "employee1", "password": "wrongpassword"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Неправильный логин или пароль"


@pytest.mark.asyncio
async def test_login_wrong_username(client: AsyncClient):
    """Вход с неправильным логином."""
    response = await client.post(
        "/auth/login",
        json={"username": "wrongusername", "password": "employee123"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Неправильный логин или пароль"
