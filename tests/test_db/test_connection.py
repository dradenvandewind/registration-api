# tests/test_db/test_connection.py
import pytest
import asyncpg
from unittest.mock import AsyncMock, patch, MagicMock
from app.db.connection import DatabasePool, db
from app.core.config import settings

@pytest.fixture
def db_pool():
    """Fixture to create a fresh DatabasePool instance for each test"""
    return DatabasePool()

def create_mock_connection():
    """Helper to create a mock connection with common setup"""
    mock_connection = AsyncMock()
    return mock_connection

def create_mock_acquire(mock_connection):
    """Helper to create a proper async context manager mock for pool.acquire()"""
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    return mock_acquire

@pytest.mark.asyncio
async def test_initialize_success(db_pool):
    """Test successful database pool initialization"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    
    with patch('asyncpg.create_pool', new_callable=AsyncMock, return_value=mock_pool) as mock_create_pool:
        await db_pool.initialize()
        
        assert db_pool.pool == mock_pool
        assert db_pool._initialized is True
        mock_create_pool.assert_called_once_with(
            settings.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        print("✅ Database pool initialized successfully")

@pytest.mark.asyncio
async def test_initialize_already_initialized(db_pool):
    """Test initialize when pool is already initialized"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    
    with patch('asyncpg.create_pool', new_callable=AsyncMock, return_value=mock_pool) as mock_create_pool:
        await db_pool.initialize()
        assert mock_create_pool.call_count == 1
        
        await db_pool.initialize()
        assert mock_create_pool.call_count == 1
        assert db_pool._initialized is True
        
        print("✅ Initialize returns early when already initialized")

@pytest.mark.asyncio
async def test_initialize_failure(db_pool):
    """Test initialize when pool creation fails"""
    with patch('asyncpg.create_pool', new_callable=AsyncMock, side_effect=Exception("Connection failed")) as mock_create_pool:
        with pytest.raises(Exception) as exc_info:
            await db_pool.initialize()
        
        assert "Connection failed" in str(exc_info.value)
        assert db_pool.pool is None
        assert db_pool._initialized is False
        mock_create_pool.assert_called_once()
        
        print("✅ Initialize properly handles connection failures")

@pytest.mark.asyncio
async def test_close_with_pool(db_pool):
    """Test closing the pool when it exists"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    await db_pool.close()
    
    mock_pool.close.assert_called_once()
    assert db_pool.pool is None
    assert db_pool._initialized is False
    
    print("✅ Pool closed successfully")

@pytest.mark.asyncio
async def test_close_without_pool(db_pool):
    """Test closing when pool is None"""
    db_pool.pool = None
    db_pool._initialized = False
    
    await db_pool.close()
    
    assert db_pool.pool is None
    assert db_pool._initialized is False
    
    print("✅ Close handles None pool gracefully")

@pytest.mark.asyncio
async def test_close_multiple_calls(db_pool):
    """Test calling close multiple times"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    await db_pool.close()
    mock_pool.close.assert_called_once()
    
    await db_pool.close()
    mock_pool.close.assert_called_once()
    
    print("✅ Multiple close calls handled correctly")

@pytest.mark.asyncio
async def test_execute_success(db_pool):
    """Test successful execute operation"""
    # Setup
    mock_connection = create_mock_connection()
    mock_connection.execute = AsyncMock(return_value="EXECUTE 1")
    
    mock_acquire = create_mock_acquire(mock_connection)
    
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)  # Pas AsyncMock, MagicMock!
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    query = "INSERT INTO test VALUES ($1)"
    args = ("value",)
    
    # Execute
    result = await db_pool.execute(query, *args)
    
    # Verify
    assert result == "EXECUTE 1"
    mock_pool.acquire.assert_called_once()
    mock_acquire.__aenter__.assert_called_once()
    mock_connection.execute.assert_called_once_with(query, *args)
    
    print("✅ execute operation successful")

@pytest.mark.asyncio
async def test_execute_without_initialization(db_pool):
    """Test execute when pool is not initialized"""
    db_pool.pool = None
    
    with pytest.raises(RuntimeError) as exc_info:
        await db_pool.execute("SELECT 1")
    
    assert "Base de données non initialisée" in str(exc_info.value)
    
    print("✅ execute raises RuntimeError when not initialized")

@pytest.mark.asyncio
async def test_fetch_success(db_pool):
    """Test successful fetch operation"""
    # Setup
    mock_rows = [{"id": 1, "name": "test"}]
    mock_connection = create_mock_connection()
    mock_connection.fetch = AsyncMock(return_value=mock_rows)
    
    mock_acquire = create_mock_acquire(mock_connection)
    
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)  # Pas AsyncMock!
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    query = "SELECT * FROM test WHERE id = $1"
    args = (1,)
    
    # Execute
    result = await db_pool.fetch(query, *args)
    
    # Verify
    assert result == mock_rows
    mock_pool.acquire.assert_called_once()
    mock_acquire.__aenter__.assert_called_once()
    mock_connection.fetch.assert_called_once_with(query, *args)
    
    print("✅ fetch operation successful")

@pytest.mark.asyncio
async def test_fetch_without_initialization(db_pool):
    """Test fetch when pool is not initialized"""
    db_pool.pool = None
    
    with pytest.raises(RuntimeError) as exc_info:
        await db_pool.fetch("SELECT 1")
    
    assert "Base de données non initialisée" in str(exc_info.value)
    
    print("✅ fetch raises RuntimeError when not initialized")

@pytest.mark.asyncio
async def test_fetchrow_success(db_pool):
    """Test successful fetchrow operation"""
    # Setup
    mock_row = {"id": 1, "name": "test"}
    mock_connection = create_mock_connection()
    mock_connection.fetchrow = AsyncMock(return_value=mock_row)
    
    mock_acquire = create_mock_acquire(mock_connection)
    
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    mock_pool.acquire = MagicMock(return_value=mock_acquire)  # Pas AsyncMock!
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    query = "SELECT * FROM test WHERE id = $1"
    args = (1,)
    
    # Execute
    result = await db_pool.fetchrow(query, *args)
    
    # Verify
    assert result == mock_row
    mock_pool.acquire.assert_called_once()
    mock_acquire.__aenter__.assert_called_once()
    mock_connection.fetchrow.assert_called_once_with(query, *args)
    
    print("✅ fetchrow operation successful")

@pytest.mark.asyncio
async def test_fetchrow_without_initialization(db_pool):
    """Test fetchrow when pool is not initialized"""
    db_pool.pool = None
    
    with pytest.raises(RuntimeError) as exc_info:
        await db_pool.fetchrow("SELECT 1")
    
    assert "Base de données non initialisée" in str(exc_info.value)
    
    print("✅ fetchrow raises RuntimeError when not initialized")

@pytest.mark.asyncio
async def test_execute_with_connection_error(db_pool):
    """Test execute when connection acquisition fails"""
    # Setup
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    
    # Créer un mock pour l'exception
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    
    mock_pool.acquire = MagicMock(return_value=mock_acquire)
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    # Execute & Verify
    with pytest.raises(Exception) as exc_info:
        await db_pool.execute("SELECT 1")
    
    assert "Connection error" in str(exc_info.value)
    print("✅ execute propagates connection errors")

@pytest.mark.asyncio
async def test_fetch_with_connection_error(db_pool):
    """Test fetch when connection acquisition fails"""
    # Setup
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    
    mock_pool.acquire = MagicMock(return_value=mock_acquire)
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    # Execute & Verify
    with pytest.raises(Exception) as exc_info:
        await db_pool.fetch("SELECT 1")
    
    assert "Connection error" in str(exc_info.value)
    print("✅ fetch propagates connection errors")

@pytest.mark.asyncio
async def test_fetchrow_with_connection_error(db_pool):
    """Test fetchrow when connection acquisition fails"""
    # Setup
    mock_pool = AsyncMock(spec=asyncpg.Pool)
    
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(side_effect=Exception("Connection error"))
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    
    mock_pool.acquire = MagicMock(return_value=mock_acquire)
    db_pool.pool = mock_pool
    db_pool._initialized = True
    
    # Execute & Verify
    with pytest.raises(Exception) as exc_info:
        await db_pool.fetchrow("SELECT 1")
    
    assert "Connection error" in str(exc_info.value)
    print("✅ fetchrow propagates connection errors")

def test_singleton_instance():
    """Test that the db singleton instance exists"""
    assert db is not None
    assert isinstance(db, DatabasePool)
    print("✅ Database singleton instance exists")