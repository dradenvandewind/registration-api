import pytest
from httpx import AsyncClient, ASGITransport
from base64 import b64encode
from app.main import app

def basic_auth_header(username: str, password: str) -> dict:
    """Génère un header Basic Auth"""
    credentials = f"{username}:{password}"
    encoded = b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

@pytest.mark.asyncio
async def test_activate_account_unauthorized():
    """Test sans authentification valide"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/activation",
            json={"code": "1234"},
            headers=basic_auth_header("wrong@email.com", "wrongpassword")
        )
        
        assert response.status_code == 401
        print("✅ Requête non autorisée correctement rejetée")

@pytest.mark.asyncio
async def test_activate_account_invalid_code():
    """Test avec code invalide"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # D\'abord créer un utilisateur
        register_response = await client.post(
            "/v1/registration",
            json={
                "email": "invalidcode@example.com",
                "password": "secure123"
            }
        )
        assert register_response.status_code == 201
        print("✅ Utilisateur créé pour le test")
        
        # Essayer avec un mauvais code
        headers = basic_auth_header("invalidcode@example.com", "secure123")
        response = await client.post(
            "/v1/activation",
            json={"code": "9999"},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
        print("✅ Code invalide correctement rejeté")
