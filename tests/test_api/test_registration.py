import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_user_success():
    """Test d\'inscription réussie"""
    transport = ASGITransport(
        app=app
        )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={
                "email": "test@example.com",
                "password": "secure"  # Mot de passe plus court
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == "test@example.com"
        assert data["is_active"] is False
        print(f"✅ Utilisateur créé: {data}")

@pytest.mark.asyncio
async def test_register_user_invalid_email():
    """Test avec email invalide"""
    transport = ASGITransport(
        app=app
        )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={
                "email": "invalid-email",
                "password": "secure123"
            }
        )
        
        assert response.status_code == 422
        print("✅ Email invalide correctement rejeté")

@pytest.mark.asyncio
async def test_register_user_short_password():
    """Test avec mot de passe trop court"""
    transport = ASGITransport(
        app=app
        )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/registration",
            json={
                "email": "test@example.com",
                "password": "short"
            }
        )
        
        assert response.status_code == 422
        print("✅ Mot de passe trop court correctement rejeté")

@pytest.mark.asyncio
async def test_register_duplicate_email():
    """Test d\'inscription avec email déjà utilisé"""
    transport = ASGITransport(
        app=app
        )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Première inscription
        response1 = await client.post(
            "/v1/registration",
            json={
                "email": "duplicate@example.com",
                "password": "secure"
            }
        )
        assert response1.status_code == 201
        print("✅ Premier utilisateur créé")
        
        # Deuxième inscription avec le même email
        response2 = await client.post(
            "/v1/registration",
            json={
                "email": "duplicate@example.com",
                "password": "another123"
            }
        )
        
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()
        print("✅ Email dupliqué correctement rejeté")
