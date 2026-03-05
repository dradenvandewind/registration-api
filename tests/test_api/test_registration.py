# tests/test_api/test_registration.py
"""
Tests de l'endpoint POST /v1/registration.
La DB est mockée via conftest.py (fixture autouse mock_db_pool).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from tests.test_api.conftest import make_user_row, make_code_row

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_row(email: str):
    """Retourne une fausse ligne DB imitant un asyncpg.Record."""
    now = datetime.utcnow()

    class FakeRow:
        _data = {
            "id": uuid4(),
            "email": email,
            "password_hash": "$2b$12$fakehash",
            "is_active": False,
            "created_at": now,
            "updated_at": now,
        }
        def __getitem__(self, k): return self._data[k]
        def keys(self): return self._data.keys()
        def items(self): return self._data.items()
        def __iter__(self): return iter(self._data)

    return FakeRow()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_user_success(mock_db_pool):
    """
    Inscription réussie : email libre → 201 avec le bon payload.
    """
    from tests.test_api.conftest import make_user_row, make_code_row
    
    fake_user_row = make_user_row("test@example.com")
    fake_code_row = make_code_row(fake_user_row._d["id"], "ABC123")
    
    call_count = 0
    
    async def fetchrow_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        query = args[0] if args else ""
        
        print(f"Appel #{call_count} - Query: {query[:50]}...")
        
        if "SELECT" in query and "users" in query:
            return None  # get_by_email
        elif "INSERT INTO users" in query:
            return fake_user_row  # create_user
        elif "INSERT INTO activation_codes" in query:
            return fake_code_row  # create_activation_code
        else:
            return None
    
    mock_db_pool.fetchrow.side_effect = fetchrow_side_effect
    
    with patch("app.api.v1.endpoints.registration.email_service.send_activation_code",
               new_callable=AsyncMock, return_value=True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/registration",
                json={"email": "test@example.com", "password": "s123"},
            )
    
    print(f"Total appels: {call_count}")
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_register_duplicate_email(mock_db_pool):
    """Email déjà utilisé → 409 Conflict."""
    from tests.test_api.conftest import make_user_row
    
    existing_row = make_user_row("duplicate@example.com")
    call_count = 0
    
    async def fetchrow_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        query = args[0] if args else ""
        
        print(f"Appel #{call_count}: {query[:100]}...")
        
        # Premier appel: vérification email
        if call_count == 1:
            return existing_row
        # Appels suivants: ne devraient pas arriver normalement
        else:
            print(f"  ⚠️ Appel inattendu #{call_count}")
            return None
    
    mock_db_pool.fetchrow.side_effect = fetchrow_side_effect
    
    with patch("app.api.v1.endpoints.registration.email_service.send_activation_code",
               new_callable=AsyncMock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/registration",
                json={"email": "duplicate@example.com", "password": "secure123"},
            )
    
    print(f"Total appels: {call_count}")
    assert response.status_code == 409 
@pytest.mark.asyncio
async def test_register_user_short_password(mock_db_pool):
    """Mot de passe trop court (< 6 chars) → 422 (validation Pydantic)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={"email": "test@example.com", "password": "ab"},
        )

    assert response.status_code == 422
    mock_db_pool.fetchrow.assert_not_called()
    print("✅ Mot de passe trop court → 422")


@pytest.mark.asyncio
async def test_register_user_missing_email(mock_db_pool):
    """Champ email absent → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={"password": "e123"},
        )

    assert response.status_code == 422
    print("✅ Email manquant → 422")


@pytest.mark.asyncio
async def test_register_user_missing_password(mock_db_pool):
    """Champ password absent → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={"email": "test@example.com"},
        )

    assert response.status_code == 422
    print("✅ Password manquant → 422")


@pytest.mark.asyncio
async def test_register_duplicate_email(mock_db_pool):
    """Email déjà utilisé → 409 Conflict."""
    existing_row = _make_user_row("duplicate@example.com")

    # fetchrow retourne une row existante → UserAlreadyExistsError
    mock_db_pool.fetchrow = AsyncMock(return_value=existing_row)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={"email": "duplicate@example.com", "password": "secure123"},
        )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()
    print("✅ Email dupliqué → 409")


@pytest.mark.asyncio
async def test_register_empty_body(mock_db_pool):
    """Body vide → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/v1/registration", json={})

    assert response.status_code == 422
    print("✅ Body vide → 422")