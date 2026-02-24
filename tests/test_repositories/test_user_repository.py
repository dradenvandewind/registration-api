# tests/test_repositories/test_user_repository.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime
from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserInDB

@pytest.fixture
def user_repository():
    """Fixture to create a UserRepository instance"""
    return UserRepository()

@pytest.fixture
def sample_user_id():
    """Fixture for a sample user UUID"""
    return uuid4()

@pytest.fixture
def sample_user_create():
    """Fixture for user creation data"""
    return UserCreate(
        email="test@example.com",
        password="secure123"
    )

@pytest.fixture
def mock_user_dict():
    """Fixture to return a real dictionary for user data"""
    user_id = uuid4()
    now = datetime.utcnow()
    
    return {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "hashed_password_123",
        "is_active": False,
        "created_at": now,
        "updated_at": now
    }

@pytest.fixture
def mock_user_row(mock_user_dict):
    """Fixture to mock a database row as a dict-like object"""
    class MockRow:
        def __init__(self, data):
            self._data = data
        
        def __getitem__(self, key):
            return self._data[key]
        
        def keys(self):
            return self._data.keys()
        
        def values(self):
            return self._data.values()
        
        def items(self):
            return self._data.items()
        
        def __iter__(self):
            return iter(self._data)
    
    return MockRow(mock_user_dict)

class TestUserRepositoryGetById:
    """Tests for get_by_id method (lines 24-26)"""
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, sample_user_id, mock_user_row, mock_user_dict):
        """
        Test successfully retrieving a user by ID
        Covers lines 24-26
        """
        with patch('app.db.repositories.user_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_user_row
            
            # Execute
            result = await user_repository.get_by_id(sample_user_id)
            
            # Verify
            assert result is not None
            assert isinstance(result, UserInDB)
            assert result.id == mock_user_dict["id"]
            assert result.email == mock_user_dict["email"]
            assert result.password_hash == mock_user_dict["password_hash"]
            assert result.is_active == mock_user_dict["is_active"]
            
            # Verify query (line 24)
            expected_query = "SELECT * FROM users WHERE id = $1"
            mock_fetchrow.assert_called_once_with(expected_query, sample_user_id)
            
            print("✅ get_by_id success path (lines 24-26)")
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository, sample_user_id):
        """
        Test get_by_id when user does not exist
        Covers line 26 (return None path)
        """
        with patch('app.db.repositories.user_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            # Execute
            result = await user_repository.get_by_id(sample_user_id)
            
            # Verify (line 26)
            assert result is None
            mock_fetchrow.assert_called_once()
            
            print("✅ get_by_id returns None when user not found (line 26)")
    
    @pytest.mark.asyncio
    async def test_get_by_id_db_error(self, user_repository, sample_user_id):
        """
        Test database error during get_by_id
        Ensures error propagation
        """
        with patch('app.db.repositories.user_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await user_repository.get_by_id(sample_user_id)
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ get_by_id propagates database errors")

class TestUserRepositoryActivateUser:
    """Tests for activate_user method (lines 29-30)"""
    
    @pytest.mark.asyncio
    async def test_activate_user_success(self, user_repository, sample_user_id):
        """
        Test successfully activating a user
        Covers lines 29-30
        """
        with patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 1"
            
            # Execute
            await user_repository.activate_user(sample_user_id)
            
            # Verify (lines 29-30)
            expected_query = "UPDATE users SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = $1"
            mock_execute.assert_called_once_with(expected_query, sample_user_id)
            
            print("✅ activate_user success path (lines 29-30)")
    
    @pytest.mark.asyncio
    async def test_activate_user_nonexistent_user(self, user_repository, sample_user_id):
        """
        Test activating a user that doesn't exist
        Should still execute (UPDATE 0 rows)
        Covers lines 29-30
        """
        with patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 0"
            
            # Execute
            await user_repository.activate_user(sample_user_id)
            
            # Verify execute was still called
            mock_execute.assert_called_once()
            
            print("✅ activate_user handles nonexistent user (lines 29-30)")
    
    @pytest.mark.asyncio
    async def test_activate_user_multiple_calls(self, user_repository, sample_user_id):
        """
        Test calling activate_user multiple times
        Covers lines 29-30 with repeated calls
        """
        with patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            # Call activate_user twice
            await user_repository.activate_user(sample_user_id)
            await user_repository.activate_user(sample_user_id)
            
            # Verify both calls were made
            assert mock_execute.call_count == 2
            expected_query = "UPDATE users SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = $1"
            
            for call in mock_execute.call_args_list:
                assert call[0][0] == expected_query
                assert call[0][1] == sample_user_id
            
            print("✅ activate_user multiple calls (lines 29-30)")
    
    @pytest.mark.asyncio
    async def test_activate_user_db_error(self, user_repository, sample_user_id):
        """
        Test database error during activate_user
        Ensures error propagation from line 30
        """
        with patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await user_repository.activate_user(sample_user_id)
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ activate_user propagates database errors")

class TestUserRepositoryUpdatePassword:
    """Tests for update_password method (lines 33-35)"""
    
    @pytest.mark.asyncio
    async def test_update_password_success(self, user_repository, sample_user_id):
        """
        Test successfully updating a user's password
        Covers lines 33-35
        """
        new_password = "new_secure_password_123"
        hashed_password = "hashed_new_password"
        
        with patch('app.db.repositories.user_repository.get_password_hash') as mock_hash, \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            mock_hash.return_value = hashed_password
            mock_execute.return_value = "UPDATE 1"
            
            # Execute
            await user_repository.update_password(sample_user_id, new_password)
            
            # Verify hash function was called (line 33)
            mock_hash.assert_called_once_with(new_password)
            
            # Verify execute was called (lines 34-35)
            expected_query = "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
            mock_execute.assert_called_once_with(expected_query, hashed_password, sample_user_id)
            
            print("✅ update_password success path (lines 33-35)")
    
    @pytest.mark.asyncio
    async def test_update_password_nonexistent_user(self, user_repository, sample_user_id):
        """
        Test updating password for a user that doesn't exist
        Should still execute (UPDATE 0 rows)
        Covers lines 33-35
        """
        new_password = "new_password"
        hashed_password = "hashed_password"
        
        with patch('app.db.repositories.user_repository.get_password_hash', return_value=hashed_password), \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            mock_execute.return_value = "UPDATE 0"
            
            # Execute
            await user_repository.update_password(sample_user_id, new_password)
            
            # Verify execute was still called
            mock_execute.assert_called_once()
            
            print("✅ update_password handles nonexistent user (lines 33-35)")
    
    @pytest.mark.asyncio
    async def test_update_password_different_users(self, user_repository):
        """
        Test updating passwords for different users
        Ensures user_id parameter is used correctly (lines 33-35)
        """
        user1_id = uuid4()
        user2_id = uuid4()
        password1 = "password1"
        password2 = "password2"
        hashed1 = "hashed1"
        hashed2 = "hashed2"
        
        with patch('app.db.repositories.user_repository.get_password_hash') as mock_hash, \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            # Configure mock to return different hashes
            mock_hash.side_effect = [hashed1, hashed2]
            
            # Update first user
            await user_repository.update_password(user1_id, password1)
            
            # Update second user
            await user_repository.update_password(user2_id, password2)
            
            # Verify calls
            assert mock_hash.call_count == 2
            assert mock_execute.call_count == 2
            
            first_call_args = mock_execute.call_args_list[0][0]
            second_call_args = mock_execute.call_args_list[1][0]
            
            expected_query = "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
            
            # First call
            assert first_call_args[0] == expected_query
            assert first_call_args[1] == hashed1
            assert first_call_args[2] == user1_id
            
            # Second call
            assert second_call_args[0] == expected_query
            assert second_call_args[1] == hashed2
            assert second_call_args[2] == user2_id
            
            print("✅ update_password correctly targets different users (lines 33-35)")
    
    @pytest.mark.asyncio
    async def test_update_password_multiple_calls_same_user(self, user_repository, sample_user_id):
        """
        Test updating password multiple times for same user
        Covers lines 33-35 with repeated calls
        """
        password1 = "first_password"
        password2 = "second_password"
        hashed1 = "hashed_first"
        hashed2 = "hashed_second"
        
        with patch('app.db.repositories.user_repository.get_password_hash') as mock_hash, \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            mock_hash.side_effect = [hashed1, hashed2]
            
            # Update twice
            await user_repository.update_password(sample_user_id, password1)
            await user_repository.update_password(sample_user_id, password2)
            
            # Verify both calls were made
            assert mock_hash.call_count == 2
            assert mock_execute.call_count == 2
            
            expected_query = "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
            
            for i, call in enumerate(mock_execute.call_args_list):
                expected_hash = hashed1 if i == 0 else hashed2
                assert call[0][0] == expected_query
                assert call[0][1] == expected_hash
                assert call[0][2] == sample_user_id
            
            print("✅ update_password multiple calls same user (lines 33-35)")
    
    @pytest.mark.asyncio
    async def test_update_password_with_special_characters(self, user_repository, sample_user_id):
        """
        Test password update with special characters
        Covers lines 33-35 with edge case input
        """
        special_password = "P@ssw0rd!$%&*()"
        hashed = "hashed_special"
        
        with patch('app.db.repositories.user_repository.get_password_hash') as mock_hash, \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            mock_hash.return_value = hashed
            
            await user_repository.update_password(sample_user_id, special_password)
            
            # Verify hash was called with special password
            mock_hash.assert_called_once_with(special_password)
            mock_execute.assert_called_once()
            
            print("✅ update_password handles special characters (lines 33-35)")
    
    @pytest.mark.asyncio
    async def test_update_password_db_error(self, user_repository, sample_user_id):
        """
        Test database error during update_password
        Ensures error propagation from line 35
        """
        with patch('app.db.repositories.user_repository.get_password_hash') as mock_hash, \
             patch('app.db.repositories.user_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            
            mock_hash.return_value = "hashed"
            mock_execute.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await user_repository.update_password(sample_user_id, "newpassword")
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ update_password propagates database errors")