# tests/test_main.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
import httpx
from app.main import app, lifespan

# Importer FastAPI pour les tests
from fastapi import FastAPI

class TestLifespan:
    """Tests for the lifespan context manager (lines 10-15)"""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup(self):
        """
        Test that lifespan initializes database on startup
        Covers line 12 (db.initialize())
        """
        # Mock db.initialize
        with patch('app.main.db.initialize', new_callable=AsyncMock) as mock_initialize:
            # Mock db.close to avoid side effects
            with patch('app.main.db.close', new_callable=AsyncMock):
                
                # Create a mock app
                mock_app = MagicMock(spec=FastAPI)
                
                # Use the lifespan context manager
                async with lifespan(mock_app) as manager:
                    # During the context, verify initialize was called
                    mock_initialize.assert_called_once()
                    
                    # Verify we can yield
                    assert manager is None
                
                print("✅ Lifespan startup calls db.initialize() (line 12)")
    
    @pytest.mark.asyncio
    async def test_lifespan_shutdown(self):
        """
        Test that lifespan closes database on shutdown
        Covers line 14 (db.close())
        """
        # Mock db.initialize to avoid side effects
        with patch('app.main.db.initialize', new_callable=AsyncMock):
            # Mock db.close
            with patch('app.main.db.close', new_callable=AsyncMock) as mock_close:
                
                # Create a mock app
                mock_app = MagicMock(spec=FastAPI)
                
                # Use the lifespan context manager
                async with lifespan(mock_app):
                    # Inside the context, close should not be called yet
                    mock_close.assert_not_called()
                
                # After exiting the context, close should be called
                mock_close.assert_called_once()
                
                print("✅ Lifespan shutdown calls db.close() (line 14)")
    
    @pytest.mark.asyncio
    async def test_lifespan_full_flow(self):
        """
        Test the complete lifespan flow
        Covers lines 10-15
        """
        # Track calls
        calls = []
        
        # Create mock with side effects to track order
        mock_db = AsyncMock()
        mock_db.initialize = AsyncMock(side_effect=lambda: calls.append("initialize"))
        mock_db.close = AsyncMock(side_effect=lambda: calls.append("close"))
        
        # Create a mock app
        mock_app = MagicMock(spec=FastAPI)
        
        with patch('app.main.db', mock_db):
            # Use lifespan
            async with lifespan(mock_app):
                # During context
                calls.append("inside")
            
            # Verify order: initialize -> inside -> close
            assert calls == ["initialize", "inside", "close"]
            
            print("✅ Lifespan follows correct order: initialize -> yield -> close (lines 10-15)")
    
    @pytest.mark.asyncio
    async def test_lifespan_initialize_error(self):
        """
        Test lifespan when initialize fails
        Ensures error handling in line 12
        """
        # Mock db.initialize to raise an exception
        with patch('app.main.db.initialize', new_callable=AsyncMock, side_effect=Exception("DB connection failed")):
            # Mock db.close to avoid side effects
            with patch('app.main.db.close', new_callable=AsyncMock):
                
                # Create a mock app
                mock_app = MagicMock(spec=FastAPI)
                
                # The context manager should raise the exception
                with pytest.raises(Exception) as exc_info:
                    async with lifespan(mock_app):
                        pass  # This should not be reached
                
                assert "DB connection failed" in str(exc_info.value)
                
                print("✅ Lifespan propagates initialize errors")

class TestFastAPIApp:
    """Tests for the FastAPI app configuration"""
    
    def test_app_creation(self):
        """Test that the FastAPI app is created with correct metadata"""
        assert app.title == "Dailymotion Registration API"
        assert app.description == "User registration and activation API"
        assert app.version == "1.0.0"
        print("✅ App created with correct metadata")
    
    def test_router_included(self):
        """Test that the v1 router is included"""
        # Check that routes from v1 router are present
        routes = [route.path for route in app.routes]
        
        # These should be included from v1 router
        assert "/v1/registration" in routes
        assert "/v1/activation" in routes
        assert "/health" in routes
        
        print("✅ v1 router included correctly")
    
    def test_exception_handlers_setup(self):
        """
        Test that exception handlers are set up
        This indirectly tests line 18 (setup_exception_handlers)
        """
        # Check that exception handlers are registered
        from app.core.exceptions import (
            UserAlreadyExistsError,
            UserNotFoundError,
            InvalidActivationCodeError,
            UserAlreadyActiveError
        )
        
        # Get all exception handlers from app
        exception_handlers = list(app.exception_handlers.keys())
        
        # Check that our custom exceptions are handled
        assert UserAlreadyExistsError in exception_handlers
        assert UserNotFoundError in exception_handlers
        assert InvalidActivationCodeError in exception_handlers
        assert UserAlreadyActiveError in exception_handlers
        
        print("✅ Exception handlers set up correctly")
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test the health check endpoint using httpx.AsyncClient"""
        # Create transport for the app
        transport = httpx.ASGITransport(app=app)
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}
        
        print("✅ Health check endpoint works")

class TestIntegration:
    """Integration tests for the whole app"""
    
    @pytest.mark.asyncio
    async def test_app_lifespan_integration(self):
        """
        Integration test for app lifespan using httpx.AsyncClient
        """
        # Create transport for the app
        transport = httpx.ASGITransport(app=app)
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Make a request to trigger lifespan
            response = await client.get("/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}
        
        print("✅ App works with httpx.AsyncClient (lifespan managed automatically)")
    
    @pytest.mark.asyncio
    async def test_app_routes_accessible(self):
        """Test that main routes are accessible using httpx.AsyncClient"""
        transport = httpx.ASGITransport(app=app)
        
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Health check (no auth required)
            response = await client.get("/health")
            assert response.status_code == 200
            
            # Registration endpoint (should return 422 with invalid data, but route exists)
            response = await client.post("/v1/registration", json={})
            assert response.status_code == 422  # Validation error means route exists
            
            # Activation endpoint (should return 401 without auth, but route exists)
            response = await client.post("/v1/activation", json={})
            assert response.status_code == 401  # Unauthorized means route exists
        
        print("✅ All main routes are accessible")