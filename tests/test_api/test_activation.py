import pytest
from httpx import AsyncClient, ASGITransport
from base64 import b64encode
from app.main import app

from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials
from app.api.v1.endpoints.activation import activate_account
from app.models.activation import ActivationRequest
from app.models.user import UserInDB
from app.core.exceptions import (
    InvalidActivationCodeError,
    UserNotFoundError,
    UserAlreadyActiveError
)

def basic_auth_header(username: str, password: str) -> dict:
    """Génère un header Basic Auth"""
    credentials = f"{username}:{password}"
    encoded = b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}

@pytest.mark.asyncio
async def test_activate_account_unauthorized():
    """Test sans authentification valide"""
    transport = ASGITransport(
        app=app
        )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/activation",
            json={"code": "123456"},
            headers=basic_auth_header("wrong@email.com", "wrongpassword")
        )
        
        assert response.status_code == 401
        print("✅ Requête non autorisée correctement rejetée")

@pytest.mark.asyncio
async def test_activate_account_invalid_code():
    """Test avec code invalide"""
    transport = ASGITransport(
        app=app
       )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        TEST_PASSWORD = "secure123"
        TEST_EMAIL = "invalidcode@example.com"
        # D\'abord créer un utilisateur
        register_response = await client.post(
            "/v1/registration",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        assert register_response.status_code == 201
        print("✅ Utilisateur créé pour le test")
        
        # Essayer avec un mauvais code
        headers = basic_auth_header(TEST_EMAIL, TEST_PASSWORD)
        response = await client.post(
            "/v1/activation",
            json={"code": "9999"},
            headers=headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
        print("✅ Code invalide correctement rejeté")

@pytest.mark.asyncio
async def test_activate_account_handles_exceptions():
    """
    Test that activate_account properly catches exceptions and raises HTTPException
    Covers line 31 (the except block that catches multiple exceptions)
    """
    # Create test data
    activation_request = ActivationRequest(code="123456")
    
    # Create a mock current user
    mock_user = UserInDB(
        id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=False,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    # Test each exception type to ensure line 31 catches them all
    exceptions_to_test = [
        (UserNotFoundError("User not found"), "User not found"),
        (UserAlreadyActiveError("User is already active"), "User is already active"),
        (InvalidActivationCodeError("Invalid or expired activation code"), "Invalid or expired activation code")
    ]
    
    for exception, expected_message in exceptions_to_test:
        # Mock the ActivationService to raise the exception
        with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.activate_user = AsyncMock(side_effect=exception)
            mock_service_class.return_value = mock_service
            
            # Execute & Verify
            with pytest.raises(HTTPException) as exc_info:
                await activate_account(activation_request, mock_user)
            
            # Verify the HTTP exception (line 31)
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail == expected_message
            
            # Verify the service was called
            mock_service.activate_user.assert_called_once_with(
                mock_user.id,
                activation_request.code
            )
    
    print("✅ Line 31: All exceptions properly caught and converted to HTTP 400")

@pytest.mark.asyncio
async def test_activate_account_user_not_found():
    """
    Test that UserNotFoundError is properly caught and converted
    Specifically tests line 31 with UserNotFoundError
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = "test-id"
    
    with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.activate_user = AsyncMock(side_effect=UserNotFoundError("User not found"))
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "User not found"
        
        print("✅ UserNotFoundError correctly handled in line 31")

@pytest.mark.asyncio
async def test_activate_account_user_already_active():
    """
    Test that UserAlreadyActiveError is properly caught and converted
    Specifically tests line 31 with UserAlreadyActiveError
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = "test-id"
    
    with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.activate_user = AsyncMock(side_effect=UserAlreadyActiveError("User is already active"))
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "User is already active"
        
        print("✅ UserAlreadyActiveError correctly handled in line 31")

@pytest.mark.asyncio
async def test_activate_account_invalid_code():
    """
    Test that InvalidActivationCodeError is properly caught and converted
    Specifically tests line 31 with InvalidActivationCodeError
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = "test-id"
    
    with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.activate_user = AsyncMock(side_effect=InvalidActivationCodeError("Invalid or expired activation code"))
        mock_service_class.return_value = mock_service
        
        with pytest.raises(HTTPException) as exc_info:
            await activate_account(activation_request, mock_user)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid or expired activation code"
        
        print("✅ InvalidActivationCodeError correctly handled in line 31")

@pytest.mark.asyncio
async def test_activate_account_success():
    """
    Test successful activation (happy path)
    Ensures line 31 is not triggered when no exception occurs
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = UserInDB(
        id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        password_hash="hashed_password",
        is_active=False,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.activate_user = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        # Execute
        response = await activate_account(activation_request, mock_user)
        
        # Verify
        assert response.message == "Account activated successfully"
        assert response.user_id == mock_user.id
        mock_service.activate_user.assert_called_once_with(
            mock_user.id,
            activation_request.code
        )
        
        print("✅ Successful activation (line 31 not triggered)")

@pytest.mark.asyncio
async def test_activate_account_unexpected_exception():
    """
    Test that unexpected exceptions are not caught by line 31
    They should propagate normally
    """
    activation_request = ActivationRequest(code="123456")
    mock_user = MagicMock(spec=UserInDB)
    mock_user.id = "test-id"
    
    with patch('app.api.v1.endpoints.activation.ActivationService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service.activate_user = AsyncMock(side_effect=Exception("Unexpected database error"))
        mock_service_class.return_value = mock_service
        
        # The exception should propagate, not be caught
        with pytest.raises(Exception) as exc_info:
            await activate_account(activation_request, mock_user)
        
        assert "Unexpected database error" in str(exc_info.value)
        assert not isinstance(exc_info.value, HTTPException)
        
        print("✅ Unexpected exceptions not caught by line 31")