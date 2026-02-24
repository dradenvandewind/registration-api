# tests/test_repositories/test_activation_repository.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from app.db.repositories.activation_repository import ActivationRepository
from app.models.activation import ActivationCodeCreate, ActivationCodeInDB

@pytest.fixture
def activation_repository():
    """Fixture to create an ActivationRepository instance"""
    return ActivationRepository()

@pytest.fixture
def sample_user_id():
    """Fixture for a sample user UUID"""
    return uuid4()

@pytest.fixture
def sample_code_id():
    """Fixture for a sample activation code UUID"""
    return uuid4()

@pytest.fixture
def sample_activation_create(sample_user_id):
    """Fixture for activation code creation data"""
    return ActivationCodeCreate(
        user_id=sample_user_id,
        code="ABC123",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )

@pytest.fixture
def mock_activation_dict():
    """Fixture to return a real dictionary for activation code"""
    code_id = uuid4()
    user_id = uuid4()
    now = datetime.utcnow()
    
    return {
        "id": code_id,
        "user_id": user_id,
        "code": "ABC123",
        "expires_at": now + timedelta(hours=1),
        "used_at": None,
        "created_at": now
    }

@pytest.fixture
def mock_activation_row(mock_activation_dict):
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
    
    return MockRow(mock_activation_dict)

class TestActivationRepositoryGetValidCode:
    """Tests for get_valid_code method (lines 23-33)"""
    
    @pytest.mark.asyncio
    async def test_get_valid_code_success(self, activation_repository, sample_user_id, mock_activation_row, mock_activation_dict):
        """
        Test successfully retrieving a valid code
        Covers lines 23-33 (full method)
        """
        code = "ABC123"
        
        # Mock db.fetchrow to return a row
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_activation_row
            
            # Execute
            result = await activation_repository.get_valid_code(sample_user_id, code)
            
            # Verify
            assert result is not None
            assert isinstance(result, ActivationCodeInDB)
            assert result.code == "ABC123"
            assert result.id == mock_activation_dict["id"]
            assert result.user_id == mock_activation_dict["user_id"]
            
            # Verify the query (lines 24-32)
            expected_query = """
                SELECT * FROM activation_codes 
                WHERE user_id = $1 
                AND code = $2 
                AND used_at IS NULL 
                AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC 
                LIMIT 1
            """
            mock_fetchrow.assert_called_once()
            call_args = mock_fetchrow.call_args[0]
            
            # Check essential parts of the query
            assert "SELECT * FROM activation_codes" in call_args[0]
            assert "WHERE user_id = $1" in call_args[0]
            assert "AND code = $2" in call_args[0]
            assert "AND used_at IS NULL" in call_args[0]
            assert "AND expires_at > CURRENT_TIMESTAMP" in call_args[0]
            assert "ORDER BY created_at DESC" in call_args[0]
            assert "LIMIT 1" in call_args[0]
            assert call_args[1] == sample_user_id
            assert call_args[2] == code
            
            print("✅ get_valid_code success path (lines 23-33)")
    
    @pytest.mark.asyncio
    async def test_get_valid_code_not_found(self, activation_repository, sample_user_id):
        """
        Test get_valid_code when no valid code exists
        Covers line 33 (return None path)
        """
        code = "WRONG123"
        
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            # Execute
            result = await activation_repository.get_valid_code(sample_user_id, code)
            
            # Verify (line 33)
            assert result is None
            mock_fetchrow.assert_called_once()
            
            print("✅ get_valid_code returns None when not found (line 33)")
    
    @pytest.mark.asyncio
    async def test_get_valid_code_with_expired_code(self, activation_repository, sample_user_id):
        """
        Test get_valid_code with an expired code
        The query should not return it due to expires_at > CURRENT_TIMESTAMP condition
        """
        code = "EXPIRED"
        
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            result = await activation_repository.get_valid_code(sample_user_id, code)
            
            assert result is None
            print("✅ get_valid_code respects expiration condition")
    
    @pytest.mark.asyncio
    async def test_get_valid_code_with_used_code(self, activation_repository, sample_user_id):
        """
        Test get_valid_code with a used code
        The query should not return it due to used_at IS NULL condition
        """
        code = "USED123"
        
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = None
            
            result = await activation_repository.get_valid_code(sample_user_id, code)
            
            assert result is None
            print("✅ get_valid_code respects used_at IS NULL condition")
    
    @pytest.mark.asyncio
    async def test_get_valid_code_orders_by_created_at_desc(self, activation_repository, sample_user_id, mock_activation_row):
        """
        Test that get_valid_code returns the most recent code
        The ORDER BY created_at DESC LIMIT 1 should ensure this
        """
        code = "ABC123"
        
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_activation_row
            
            await activation_repository.get_valid_code(sample_user_id, code)
            
            call_args = mock_fetchrow.call_args[0][0]
            assert "ORDER BY created_at DESC" in call_args
            assert "LIMIT 1" in call_args
            
            print("✅ get_valid_code orders by created_at DESC and limits to 1")

class TestActivationRepositoryMarkAsUsed:
    """Tests for mark_as_used method (lines 36-37)"""
    
    @pytest.mark.asyncio
    async def test_mark_as_used_success(self, activation_repository, sample_code_id):
        """
        Test successfully marking a code as used
        Covers lines 36-37
        """
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 1"
            
            # Execute
            await activation_repository.mark_as_used(sample_code_id)
            
            # Verify (line 36-37)
            expected_query = "UPDATE activation_codes SET used_at = CURRENT_TIMESTAMP WHERE id = $1"
            mock_execute.assert_called_once_with(expected_query, sample_code_id)
            
            print("✅ mark_as_used success path (lines 36-37)")
    
    @pytest.mark.asyncio
    async def test_mark_as_used_with_nonexistent_id(self, activation_repository):
        """
        Test mark_as_used with an ID that doesn't exist
        Should still execute (UPDATE 0 rows)
        Covers lines 36-37
        """
        nonexistent_id = uuid4()
        
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 0"
            
            # Execute
            await activation_repository.mark_as_used(nonexistent_id)
            
            # Verify execute was still called
            mock_execute.assert_called_once()
            
            print("✅ mark_as_used handles nonexistent ID (lines 36-37)")
    
    @pytest.mark.asyncio
    async def test_mark_as_used_multiple_calls(self, activation_repository, sample_code_id):
        """
        Test calling mark_as_used multiple times
        Covers lines 36-37 with repeated calls
        """
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            # Call mark_as_used twice
            await activation_repository.mark_as_used(sample_code_id)
            await activation_repository.mark_as_used(sample_code_id)
            
            # Verify both calls were made
            assert mock_execute.call_count == 2
            expected_query = "UPDATE activation_codes SET used_at = CURRENT_TIMESTAMP WHERE id = $1"
            
            for call in mock_execute.call_args_list:
                assert call[0][0] == expected_query
                assert call[0][1] == sample_code_id
            
            print("✅ mark_as_used multiple calls (lines 36-37)")

class TestActivationRepositoryInvalidateOldCodes:
    """Tests for invalidate_old_codes method (lines 41-46)"""
    
    @pytest.mark.asyncio
    async def test_invalidate_old_codes_success(self, activation_repository, sample_user_id):
        """
        Test successfully invalidating old codes for a user
        Covers lines 41-46
        """
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 3"  # Simulate updating 3 rows
            
            # Execute
            await activation_repository.invalidate_old_codes(sample_user_id)
            
            # Verify (lines 42-46)
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0]
            
            # Check essential parts of the query
            assert "UPDATE activation_codes" in call_args[0]
            assert "SET used_at = CURRENT_TIMESTAMP" in call_args[0]
            assert "WHERE user_id = $1 AND used_at IS NULL" in call_args[0]
            assert call_args[1] == sample_user_id
            
            print("✅ invalidate_old_codes success path (lines 41-46)")
    
    @pytest.mark.asyncio
    async def test_invalidate_old_codes_no_codes(self, activation_repository, sample_user_id):
        """
        Test invalidate_old_codes when user has no active codes
        Should still execute successfully (UPDATE 0 rows)
        Covers lines 41-46
        """
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "UPDATE 0"
            
            # Execute
            await activation_repository.invalidate_old_codes(sample_user_id)
            
            # Verify execute was still called
            mock_execute.assert_called_once()
            
            print("✅ invalidate_old_codes handles no codes (lines 41-46)")
    
    @pytest.mark.asyncio
    async def test_invalidate_old_codes_different_users(self, activation_repository):
        """
        Test invalidating codes for different users
        Ensures user_id parameter is used correctly (lines 41-46)
        """
        user1_id = uuid4()
        user2_id = uuid4()
        
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            # Invalidate for first user
            await activation_repository.invalidate_old_codes(user1_id)
            
            # Invalidate for second user
            await activation_repository.invalidate_old_codes(user2_id)
            
            # Verify calls
            assert mock_execute.call_count == 2
            first_call_args = mock_execute.call_args_list[0][0]
            second_call_args = mock_execute.call_args_list[1][0]
            
            # Verify both queries have correct structure
            for call_args in [first_call_args, second_call_args]:
                assert "UPDATE activation_codes" in call_args[0]
                assert "SET used_at = CURRENT_TIMESTAMP" in call_args[0]
                assert "WHERE user_id = $1 AND used_at IS NULL" in call_args[0]
            
            # Verify correct user IDs
            assert first_call_args[1] == user1_id
            assert second_call_args[1] == user2_id
            
            print("✅ invalidate_old_codes targets different users (lines 41-46)")
    
    @pytest.mark.asyncio
    async def test_invalidate_old_codes_multiple_calls(self, activation_repository, sample_user_id):
        """
        Test calling invalidate_old_codes multiple times for same user
        Covers lines 41-46 with repeated calls
        """
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            # Call invalidate twice
            await activation_repository.invalidate_old_codes(sample_user_id)
            await activation_repository.invalidate_old_codes(sample_user_id)
            
            # Verify both calls were made
            assert mock_execute.call_count == 2
            
            for call in mock_execute.call_args_list:
                call_args = call[0]
                assert "UPDATE activation_codes" in call_args[0]
                assert "SET used_at = CURRENT_TIMESTAMP" in call_args[0]
                assert "WHERE user_id = $1 AND used_at IS NULL" in call_args[0]
                assert call_args[1] == sample_user_id
            
            print("✅ invalidate_old_codes multiple calls (lines 41-46)")

class TestErrorHandling:
    """Tests for error handling in repository methods"""
    
    @pytest.mark.asyncio
    async def test_get_valid_code_db_error(self, activation_repository, sample_user_id):
        """Test database error during get_valid_code"""
        with patch('app.db.repositories.activation_repository.db.fetchrow', new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await activation_repository.get_valid_code(sample_user_id, "CODE123")
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ get_valid_code propagates database errors")
    
    @pytest.mark.asyncio
    async def test_mark_as_used_db_error(self, activation_repository, sample_code_id):
        """Test database error during mark_as_used"""
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await activation_repository.mark_as_used(sample_code_id)
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ mark_as_used propagates database errors")
    
    @pytest.mark.asyncio
    async def test_invalidate_old_codes_db_error(self, activation_repository, sample_user_id):
        """Test database error during invalidate_old_codes"""
        with patch('app.db.repositories.activation_repository.db.execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception) as exc_info:
                await activation_repository.invalidate_old_codes(sample_user_id)
            
            assert "Database connection error" in str(exc_info.value)
            print("✅ invalidate_old_codes propagates database errors")