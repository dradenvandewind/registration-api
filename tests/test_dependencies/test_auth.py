# tests/test_dependencies/test_auth.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials
from app.dependencies.auth import get_current_user
from app.core.exceptions import UserNotFoundError

@pytest.mark.asyncio
async def test_get_current_user_user_not_found_error():
    """
    Test get_current_user when UserNotFoundError is raised
    Covers line 29 (except UserNotFoundError block)
    """
    # Setup
    credentials = HTTPBasicCredentials(
        username="nonexistent@example.com",
        password="somepassword"
    )
    
    # Mock UserService
    mock_user_service = AsyncMock()
    mock_user_service.verify_credentials = AsyncMock(side_effect=UserNotFoundError("User not found"))
    
    # Patch the UserService instantiation
    with patch('app.dependencies.auth.UserService', return_value=mock_user_service):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        # Verify the HTTP exception
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}
        
        # Verify the service was called correctly
        mock_user_service.verify_credentials.assert_called_once_with(
            "nonexistent@example.com",
            "somepassword"
        )
        
        print("✅ HTTPException raised with 401 status when UserNotFoundError occurs")

@pytest.mark.asyncio
async def test_get_current_user_invalid_credentials():
    """
    Test get_current_user when verify_credentials returns None
    Covers the 'if not user' block (lines 19-24)
    """
    # Setup
    credentials = HTTPBasicCredentials(
        username="user@example.com",
        password="wrongpassword"
    )
    
    # Mock UserService to return None (invalid credentials)
    mock_user_service = AsyncMock()
    mock_user_service.verify_credentials = AsyncMock(return_value=None)
    
    with patch('app.dependencies.auth.UserService', return_value=mock_user_service):
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}
        
        mock_user_service.verify_credentials.assert_called_once_with(
            "user@example.com",
            "wrongpassword"
        )
        
        print("✅ HTTPException raised with 401 status for invalid credentials")

@pytest.mark.asyncio
async def test_get_current_user_success():
    """
    Test get_current_user with valid credentials
    Covers the success path
    """
    # Setup
    credentials = HTTPBasicCredentials(
        username="valid@example.com",
        password="correctpassword"
    )
    
    # Mock user object
    mock_user = MagicMock()
    mock_user.email = "valid@example.com"
    mock_user.is_active = False
    
    # Mock UserService to return a user
    mock_user_service = AsyncMock()
    mock_user_service.verify_credentials = AsyncMock(return_value=mock_user)
    
    with patch('app.dependencies.auth.UserService', return_value=mock_user_service):
        # Execute
        result = await get_current_user(credentials)
        
        # Verify
        assert result == mock_user
        mock_user_service.verify_credentials.assert_called_once_with(
            "valid@example.com",
            "correctpassword"
        )
        
        print("✅ User returned successfully for valid credentials")

@pytest.mark.asyncio
async def test_get_current_user_unexpected_exception():
    """
    Test get_current_user when an unexpected exception occurs
    This ensures we don't mask other exceptions
    """
    # Setup
    credentials = HTTPBasicCredentials(
        username="test@example.com",
        password="password"
    )
    
    # Mock UserService to raise an unexpected exception
    mock_user_service = AsyncMock()
    mock_user_service.verify_credentials = AsyncMock(side_effect=Exception("Database connection error"))
    
    with patch('app.dependencies.auth.UserService', return_value=mock_user_service):
        # Execute & Verify - exception should propagate
        with pytest.raises(Exception) as exc_info:
            await get_current_user(credentials)
        
        assert "Database connection error" in str(exc_info.value)
        mock_user_service.verify_credentials.assert_called_once()
        
        print("✅ Unexpected exceptions propagate correctly")