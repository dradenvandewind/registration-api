# tests/test_core/test_exceptions.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status, FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from app.core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidActivationCodeError,
    UserAlreadyActiveError,
    setup_exception_handlers
)

@pytest.fixture
def mock_app():
    """Fixture to create a mock FastAPI app"""
    app = MagicMock(spec=FastAPI)
    
    # Stocker les handlers dans un dictionnaire
    app.handlers = {}
    
    def mock_exception_handler(exception_class):
        def decorator(func):
            app.handlers[exception_class] = func
            return func
        return decorator
    
    app.exception_handler.side_effect = mock_exception_handler
    return app

@pytest.fixture
def mock_request():
    """Fixture to create a mock request"""
    request = AsyncMock(spec=Request)
    return request

class TestExceptionHandlers:
    """Tests for exception handler setup and individual handlers"""
    
    def test_setup_exception_handlers_registers_all_handlers(self, mock_app):
        """
        Test that setup_exception_handlers registers all exception handlers
        """
        # Execute
        setup_exception_handlers(mock_app)
        
        # Verify that exception_handler was called for each exception type
        assert mock_app.exception_handler.call_count == 4
        
        # Verify all handlers are stored
        assert UserAlreadyExistsError in mock_app.handlers
        assert UserNotFoundError in mock_app.handlers
        assert InvalidActivationCodeError in mock_app.handlers
        assert UserAlreadyActiveError in mock_app.handlers
        
        print("✅ All exception handlers registered correctly")
    
    @pytest.mark.asyncio
    async def test_user_already_exists_handler_raises_409(self, mock_app, mock_request):
        """
        Test that UserAlreadyExistsError handler raises HTTP 409 Conflict
        Covers line 26
        """
        # Setup
        setup_exception_handlers(mock_app)
        handler = mock_app.handlers[UserAlreadyExistsError]
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            # Appeler le handler directement (c'est une coroutine)
            await handler(mock_request, UserAlreadyExistsError())
        
        # Verify status code and detail (line 26)
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "User with this email already exists"
        
        print("✅ UserAlreadyExistsError handler raises 409 Conflict (line 26)")
    
    @pytest.mark.asyncio
    async def test_user_not_found_handler_raises_404(self, mock_app, mock_request):
        """
        Test that UserNotFoundError handler raises HTTP 404 Not Found
        Covers line 33
        """
        # Setup
        setup_exception_handlers(mock_app)
        handler = mock_app.handlers[UserNotFoundError]
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request, UserNotFoundError())
        
        # Verify status code and detail (line 33)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"
        
        print("✅ UserNotFoundError handler raises 404 Not Found (line 33)")
    
    @pytest.mark.asyncio
    async def test_invalid_activation_code_handler_raises_400(self, mock_app, mock_request):
        """
        Test that InvalidActivationCodeError handler raises HTTP 400 Bad Request
        Covers line 40
        """
        # Setup
        setup_exception_handlers(mock_app)
        handler = mock_app.handlers[InvalidActivationCodeError]
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request, InvalidActivationCodeError())
        
        # Verify status code and detail (line 40)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Invalid or expired activation code"
        
        print("✅ InvalidActivationCodeError handler raises 400 Bad Request (line 40)")
    
    @pytest.mark.asyncio
    async def test_user_already_active_handler_raises_400(self, mock_app, mock_request):
        """
        Test that UserAlreadyActiveError handler raises HTTP 400 Bad Request
        Covers line 47
        """
        # Setup
        setup_exception_handlers(mock_app)
        handler = mock_app.handlers[UserAlreadyActiveError]
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await handler(mock_request, UserAlreadyActiveError())
        
        # Verify status code and detail (line 47)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "User is already active"
        
        print("✅ UserAlreadyActiveError handler raises 400 Bad Request (line 47)")
    
    def test_exception_classes_are_defined(self):
        """
        Test that all exception classes are properly defined
        """
        assert issubclass(UserAlreadyExistsError, Exception)
        assert issubclass(UserNotFoundError, Exception)
        assert issubclass(InvalidActivationCodeError, Exception)
        assert issubclass(UserAlreadyActiveError, Exception)
        
        # Test instantiation
        assert isinstance(UserAlreadyExistsError(), Exception)
        assert isinstance(UserNotFoundError(), Exception)
        assert isinstance(InvalidActivationCodeError(), Exception)
        assert isinstance(UserAlreadyActiveError(), Exception)
        
        print("✅ All exception classes are properly defined")
