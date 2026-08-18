import base64
import json
import uuid
from datetime import datetime, UTC

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.users.infrastructure.models import UserModel
from app.shared.application.passwords import PasswordService
from app.shared.infrastructure.db.session import SessionLocal


def _decode_payload(token: str) -> dict:
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())


@pytest.mark.asyncio
async def test_password_reset_revokes_old_refresh_token():
    email = f"pwreset-{uuid.uuid4().hex[:8]}@example.com"
    password = "StartPass123!"
    new_password = "NewPass123!"
    now = datetime.now(UTC)
    user_id = str(uuid.uuid4())

    password_service = PasswordService()

    async with SessionLocal() as session:
        user = UserModel(
            id=user_id,
            status="active",
            email=email,
            password_hash=password_service.hash_password(password),
            first_name="Test",
            last_name="User",
            display_name="Test User",
            phone=None,
            locale="sk",
            timezone="Europe/Bratislava",
            last_login_at=None,
            created_at=now,
            created_by_user_id=None,
            updated_at=now,
            updated_by_user_id=None,
        )
        session.add(user)
        await session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        login_data = login.json()

        assert "accessToken" in login_data
        assert "refreshToken" in login_data

        access_payload = _decode_payload(login_data["accessToken"])
        refresh_payload = _decode_payload(login_data["refreshToken"])

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert "iat" in access_payload
        assert "iat" in refresh_payload

        forgot = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot.status_code == 200, forgot.text
        forgot_data = forgot.json()

        assert forgot_data["ok"] is True
        assert "resetToken" in forgot_data

        reset = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": forgot_data["resetToken"],
                "newPassword": new_password,
            },
        )
        assert reset.status_code == 200, reset.text

        old_refresh = await client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": login_data["refreshToken"]},
        )
        assert old_refresh.status_code == 401, old_refresh.text

        reuse_reset = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": forgot_data["resetToken"],
                "newPassword": "AnotherPass123!",
            },
        )
        assert reuse_reset.status_code in (400, 401, 422), reuse_reset.text

        login_old_password = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_old_password.status_code in (400, 401), login_old_password.text

        login_new_password = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )
        assert login_new_password.status_code == 200, login_new_password.text
