# tests/test_services/test_activation_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from app.services.activation_service import ActivationService
from app.models.activation import ActivationCodeCreate, ActivationCodeInDB
from app.models.user import UserInDB
from app.core.exceptions import (
    InvalidActivationCodeError,
    UserNotFoundError,
    UserAlreadyActiveError
)
from app.db.repositories.activation_repository import ActivationRepository
from app.db.repositories.user_repository import UserRepository

@pytest.fixture
def activation_service():
    """Fixture to create an ActivationService instance with mocked repositories"""
    service = ActivationService()
    service.activation_repo = AsyncMock(spec=ActivationRepository)
    service.user_repo = AsyncMock(spec=UserRepository)
    return service

@pytest.fixture
def sample_user_id():
    """Fixture for a sample user UUID"""
    return uuid4()

@pytest.fixture
def sample_code_id():
    """Fixture for a sample activation code UUID"""
    return uuid4()

@pytest.fixture
def inactive_user(sample_user_id):
    """Fixture for an inactive user"""
    return UserInDB(
        id=sample_user_id,
        email="test@example.com",
        password_hash="hashed_password",
        is_active=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def active_user(sample_user_id):
    """Fixture for an active user"""
    return UserInDB(
        id=sample_user_id,
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def valid_activation_code(sample_user_id, sample_code_id):
    """Fixture for a valid activation code"""
    now = datetime.utcnow()
    return ActivationCodeInDB(
        id=sample_code_id,
        user_id=sample_user_id,
        code="ABC123",
        expires_at=now + timedelta(hours=1),
        used_at=None,
        created_at=now
    )

class TestActivationServiceActivateUser:
    """Tests for activate_user method"""
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, activation_service, sample_user_id, inactive_user, valid_activation_code):
        """
        Test successful user activation with valid code
        Covers lines 52-78 (full success path)
        """
        code = "ABC123"
        
        # Mock repository responses
        activation_service.user_repo.get_by_id.return_value = inactive_user
        activation_service.activation_repo.get_valid_code.return_value = valid_activation_code
        activation_service.activation_repo.mark_as_used = AsyncMock()
        activation_service.user_repo.activate_user = AsyncMock()
        
        # Execute
        result = await activation_service.activate_user(sample_user_id, code)
        
        # Verify
        assert result is True
        
        # Verify user existence check (lines 52-54)
        activation_service.user_repo.get_by_id.assert_called_once_with(sample_user_id)
        
        # Verify code validation (lines 59-62)
        activation_service.activation_repo.get_valid_code.assert_called_once_with(sample_user_id, code)
        
        # Verify mark as used (line 65)
        activation_service.activation_repo.mark_as_used.assert_called_once_with(valid_activation_code.id)
        
        # Verify user activation (line 68)
        activation_service.user_repo.activate_user.assert_called_once_with(sample_user_id)
        
        print("✅ activate_user success path (lines 52-78)")
    
    @pytest.mark.asyncio
    async def test_activate_user_not_found(self, activation_service, sample_user_id):
        """
        Test activation when user doesn't exist
        Covers lines 52-54 (UserNotFoundError)
        """
        code = "ABC123"
        
        # Mock user not found
        activation_service.user_repo.get_by_id.return_value = None
        
        # Execute & Verify
        with pytest.raises(UserNotFoundError) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "User not found" in str(exc_info.value)
        
        # Verify user existence check was called (lines 52-54)
        activation_service.user_repo.get_by_id.assert_called_once_with(sample_user_id)
        
        # Verify no further calls were made
        activation_service.activation_repo.get_valid_code.assert_not_called()
        activation_service.activation_repo.mark_as_used.assert_not_called()
        activation_service.user_repo.activate_user.assert_not_called()
        
        print("✅ activate_user raises UserNotFoundError when user doesn't exist (lines 52-54)")
    
    @pytest.mark.asyncio
    async def test_activate_user_already_active(self, activation_service, sample_user_id, active_user):
        """
        Test activation when user is already active
        Covers lines 56-58 (UserAlreadyActiveError)
        """
        code = "ABC123"
        
        # Mock user already active
        activation_service.user_repo.get_by_id.return_value = active_user
        
        # Execute & Verify
        with pytest.raises(UserAlreadyActiveError) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "User is already active" in str(exc_info.value)
        
        # Verify user existence check (lines 52-54)
        activation_service.user_repo.get_by_id.assert_called_once_with(sample_user_id)
        
        # Verify is_active check (line 57) triggered the exception
        
        # Verify no further calls were made
        activation_service.activation_repo.get_valid_code.assert_not_called()
        activation_service.activation_repo.mark_as_used.assert_not_called()
        activation_service.user_repo.activate_user.assert_not_called()
        
        print("✅ activate_user raises UserAlreadyActiveError when user is active (lines 56-58)")
    
    @pytest.mark.asyncio
    async def test_activate_user_invalid_code(self, activation_service, sample_user_id, inactive_user):
        """
        Test activation with invalid/expired code
        Covers lines 59-63 (InvalidActivationCodeError)
        """
        code = "WRONG123"
        
        # Mock user exists but is inactive
        activation_service.user_repo.get_by_id.return_value = inactive_user
        
        # Mock no valid code found
        activation_service.activation_repo.get_valid_code.return_value = None
        
        # Execute & Verify
        with pytest.raises(InvalidActivationCodeError) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Invalid or expired activation code" in str(exc_info.value)
        
        # Verify user existence check (lines 52-54)
        activation_service.user_repo.get_by_id.assert_called_once_with(sample_user_id)
        
        # Verify code validation (lines 59-62)
        activation_service.activation_repo.get_valid_code.assert_called_once_with(sample_user_id, code)
        
        # Verify no further calls were made
        activation_service.activation_repo.mark_as_used.assert_not_called()
        activation_service.user_repo.activate_user.assert_not_called()
        
        print("✅ activate_user raises InvalidActivationCodeError for invalid code (lines 59-63)")
    
    @pytest.mark.asyncio
    async def test_activate_user_with_expired_code(self, activation_service, sample_user_id, inactive_user):
        """
        Test activation with an expired code
        Should raise InvalidActivationCodeError
        Covers lines 59-63
        """
        code = "EXPIRED"
        
        # Mock user exists but is inactive
        activation_service.user_repo.get_by_id.return_value = inactive_user
        
        # Mock get_valid_code returning None (expired codes not returned)
        activation_service.activation_repo.get_valid_code.return_value = None
        
        # Execute & Verify
        with pytest.raises(InvalidActivationCodeError) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Invalid or expired activation code" in str(exc_info.value)
        
        # Verify code validation was called (lines 59-62)
        activation_service.activation_repo.get_valid_code.assert_called_once_with(sample_user_id, code)
        
        print("✅ activate_user handles expired codes correctly (lines 59-63)")
    
    @pytest.mark.asyncio
    async def test_activate_user_with_used_code(self, activation_service, sample_user_id, inactive_user):
        """
        Test activation with a code that has already been used
        Should raise InvalidActivationCodeError
        Covers lines 59-63
        """
        code = "USED123"
        
        # Mock user exists but is inactive
        activation_service.user_repo.get_by_id.return_value = inactive_user
        
        # Mock get_valid_code returning None (used codes not returned due to used_at IS NULL)
        activation_service.activation_repo.get_valid_code.return_value = None
        
        # Execute & Verify
        with pytest.raises(InvalidActivationCodeError) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Invalid or expired activation code" in str(exc_info.value)
        
        print("✅ activate_user handles used codes correctly (lines 59-63)")
    
    @pytest.mark.asyncio
    async def test_activate_user_mark_as_used_error(self, activation_service, sample_user_id, inactive_user, valid_activation_code):
        """
        Test when mark_as_used fails
        Ensures error propagation from line 65
        """
        code = "ABC123"
        
        # Mock repository responses
        activation_service.user_repo.get_by_id.return_value = inactive_user
        activation_service.activation_repo.get_valid_code.return_value = valid_activation_code
        
        # Mock mark_as_used to fail
        activation_service.activation_repo.mark_as_used = AsyncMock(side_effect=Exception("Database error"))
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Database error" in str(exc_info.value)
        
        # Verify mark_as_used was called (line 65)
        activation_service.activation_repo.mark_as_used.assert_called_once_with(valid_activation_code.id)
        
        # Verify activate_user was NOT called (should fail before line 68)
        activation_service.user_repo.activate_user.assert_not_called()
        
        print("✅ activate_user propagates errors from mark_as_used (line 65)")
    
    @pytest.mark.asyncio
    async def test_activate_user_activate_error(self, activation_service, sample_user_id, inactive_user, valid_activation_code):
        """
        Test when activate_user repository call fails
        Ensures error propagation from line 68
        """
        code = "ABC123"
        
        # Mock repository responses
        activation_service.user_repo.get_by_id.return_value = inactive_user
        activation_service.activation_repo.get_valid_code.return_value = valid_activation_code
        activation_service.activation_repo.mark_as_used = AsyncMock()
        
        # Mock activate_user to fail
        activation_service.user_repo.activate_user = AsyncMock(side_effect=Exception("Database error"))
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Database error" in str(exc_info.value)
        
        # Verify both previous calls were made
        activation_service.activation_repo.mark_as_used.assert_called_once_with(valid_activation_code.id)
        activation_service.user_repo.activate_user.assert_called_once_with(sample_user_id)
        
        print("✅ activate_user propagates errors from activate_user repository call (line 68)")
    
    @pytest.mark.asyncio
    async def test_activate_user_get_valid_code_error(self, activation_service, sample_user_id, inactive_user):
        """
        Test when get_valid_code repository call fails
        Ensures error propagation from line 59
        """
        code = "ABC123"
        
        # Mock user exists
        activation_service.user_repo.get_by_id.return_value = inactive_user
        
        # Mock get_valid_code to fail
        activation_service.activation_repo.get_valid_code = AsyncMock(side_effect=Exception("Database error"))
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Database error" in str(exc_info.value)
        
        # Verify get_valid_code was called (line 59)
        activation_service.activation_repo.get_valid_code.assert_called_once_with(sample_user_id, code)
        
        # Verify no further calls
        activation_service.activation_repo.mark_as_used.assert_not_called()
        activation_service.user_repo.activate_user.assert_not_called()
        
        print("✅ activate_user propagates errors from get_valid_code (line 59)")
    
    @pytest.mark.asyncio
    async def test_activate_user_get_by_id_error(self, activation_service, sample_user_id):
        """
        Test when get_by_id repository call fails
        Ensures error propagation from line 52
        """
        code = "ABC123"
        
        # Mock get_by_id to fail
        activation_service.user_repo.get_by_id = AsyncMock(side_effect=Exception("Database error"))
        
        # Execute & Verify
        with pytest.raises(Exception) as exc_info:
            await activation_service.activate_user(sample_user_id, code)
        
        assert "Database error" in str(exc_info.value)
        
        # Verify get_by_id was called (line 52)
        activation_service.user_repo.get_by_id.assert_called_once_with(sample_user_id)
        
        print("✅ activate_user propagates errors from get_by_id (line 52)")