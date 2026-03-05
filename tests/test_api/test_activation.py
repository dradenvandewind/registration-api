# tests/test_api/test_activation.py
"""
Tests de l'endpoint POST /v1/activation.
Les tests unitaires (mock ActivationService) gardent leur logique d'origine.
Les tests d'intégration légère (ASGITransport) utilisent mock_db_pool du conftest.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from base64 import b64encode
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials

from app.main import app
from app.api.v1.endpoints.activation import activate_account
from app.models.activation import ActivationRequest
from app.models.user import UserInDB
from app.core.exceptions import (
    InvalidActivationCodeError,
    UserNotFoundError,
    UserAlreadyActiveError,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def basic_auth_header(username: str, password: str) -> dict:
    encoded = b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _make_user_row(email: str, is_active: bool = False):
    now = datetime.utcnow()

    class FakeRow:
        _d = {
            "id": uuid4(),
            "email": email,
            "password_hash": "$2b$12$fakehash",
            "is_active": is_active,
            "created_at": now,
            "updated_at": now,
        }
        def __getitem__(self, k): return self._d[k]
        def keys(self): return self._d.keys()
        def items(self): return self._d.items()
        def __iter__(self): return iter(self._d)

    return FakeRow()


def _make_code_row(user_id, code: str):
    now = datetime.utcnow()

    class FakeRow:
        _d = {
            "id": uuid4(),
            "user_id": user_id,
            "code": code,
            "expires_at": now + timedelta(hours=1),
            "used_at": None,
            "created_at": now,
        }
        def __getitem__(self, k): return self._d[k]
        def keys(self): return self._d.keys()
        def items(self): return self._d.items()
        def __iter__(self): return iter(self._d)

    return FakeRow()


# ---------------------------------------------------------------------------
# Tests d'intégration légère (via ASGITransport + mock DB)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activate_account_unauthorized(mock_db_pool):
    """
    Identifiants inexistants → 401.
    fetchrow retourne None = utilisateur inconnu.
    """
    mock_db_pool.fetchrow = AsyncMock(return_value=None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/activation",
            json={"code": "123456"},
            headers=basic_auth_header("wrong@email.com", "wrongpassword"),
        )

    assert response.status_code == 401
    print("✅ Requête non autorisée correctement rejetée")


@pytest.mark.asyncio
async def test_activate_account_no_auth(mock_db_pool):
    """Sans header Authorization → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/activation", json={"code": "123456"})

    assert response.status_code == 401
    print("✅ Absence d'authentification → 401")


@pytest.mark.asyncio
async def test_activate_account_invalid_code(mock_db_pool):
    """
    Utilisateur authentifié mais code invalide → 400.
    On simule : fetchrow(email) → user_row, fetchrow(code) → None.
    """
    user_row = _make_user_row("validuser@example.com")
    # Séquence : 1) get_by_email (auth) → user_row,
    #            2) get_by_id (activate_user) → user_row,
    #            3) get_valid_code → None  (code invalide)
    mock_db_pool.fetchrow = AsyncMock(side_effect=[user_row, user_row, None])

    # verify_password doit retourner True pour passer l'auth
    with patch("app.core.security.bcrypt.checkpw", return_value=True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/activation",
                json={"code": "BADCODE"},
                headers=basic_auth_header("validuser@example.com", "anypassword"),
            )

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()
    print("✅ Code invalide → 400")


# ---------------------------------------------------------------------------
# Tests unitaires (mock direct du service)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activate_account_handles_all_exceptions():
    """
    Vérifie que les 3 exceptions métier sont converties en HTTP 400.
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = UserInDB(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed",
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    cases = [
        UserNotFoundError("User not found"),
        UserAlreadyActiveError("User is already active"),
        InvalidActivationCodeError("Invalid or expired activation code"),
    ]

    for exc in cases:
        with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
            svc = AsyncMock()
            svc.activate_user = AsyncMock(side_effect=exc)
            MockSvc.return_value = svc

            with pytest.raises(HTTPException) as exc_info:
                await activate_account(activation_request, mock_user)

            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == str(exc)

    print("✅ Les 3 exceptions métier → HTTP 400")


@pytest.mark.asyncio
async def test_activate_account_success_unit():
    """Chemin nominal : retourne le message de succès."""
    activation_request = ActivationRequest(code="ABC123")
    mock_user = UserInDB(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed",
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
        svc = AsyncMock()
        svc.activate_user = AsyncMock(return_value=True)
        MockSvc.return_value = svc

        response = await activate_account(activation_request, mock_user)

    assert response.message == "Account activated successfully"
    assert response.user_id == mock_user.id
    print("✅ Activation réussie → message correct")


@pytest.mark.asyncio
async def test_activate_account_unexpected_exception_propagates():
    """Une exception inattendue ne doit PAS être absorbée par le endpoint."""
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = uuid4()

    with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
        svc = AsyncMock()
        svc.activate_user = AsyncMock(side_effect=Exception("DB crash"))
        MockSvc.return_value = svc

        with pytest.raises(Exception) as exc_info:
            await activate_account(activation_request, mock_user)

    assert "DB crash" in str(exc_info.value)
    assert not isinstance(exc_info.value, HTTPException)
    print("✅ Exception inattendue propagée (non absorbée)")


@pytest.mark.asyncio
async def test_activate_user_not_found_unit():
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = uuid4()

    with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
        svc = AsyncMock()
        svc.activate_user = AsyncMock(side_effect=UserNotFoundError("User not found"))
        MockSvc.return_value = svc

        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User not found"
    print("✅ UserNotFoundError → 400")


@pytest.mark.asyncio
async def test_activate_user_already_active_unit():
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = uuid4()

    with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
        svc = AsyncMock()
        svc.activate_user = AsyncMock(side_effect=UserAlreadyActiveError("User is already active"))
        MockSvc.return_value = svc

        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "User is already active"
    print("✅ UserAlreadyActiveError → 400")


@pytest.mark.asyncio
async def test_activate_invalid_code_unit():
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = uuid4()

    with patch("app.api.v1.endpoints.activation.ActivationService") as MockSvc:
        svc = AsyncMock()
        svc.activate_user = AsyncMock(
            side_effect=InvalidActivationCodeError("Invalid or expired activation code")
        )
        MockSvc.return_value = svc

        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired activation code"
    print("✅ InvalidActivationCodeError → 400")