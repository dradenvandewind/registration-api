# tests/test_services/test_email_service.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.email_service import EmailService, email_service

@pytest.fixture
def email_service_instance():
    """Fixture to create a clean EmailService instance"""
    return EmailService()

@pytest.mark.asyncio
async def test_email_service_context_manager(email_service_instance):
    """
    Test the context manager (__aenter__ and __aexit__)
    Covers lines 11-12
    """
    # Use as context manager
    async with email_service_instance as service:
        assert service.client is not None
        assert isinstance(service.client, httpx.AsyncClient)
    
    # After exiting the context manager, the client is closed
    # Note: we can't directly verify as aclose() is called
    print("✅ Context manager works correctly")

@pytest.mark.asyncio
async def test_send_activation_code_success(email_service_instance):
    """
    Test successful email sending
    Covers lines 15-16 (beginning of the method)
    """
    # Setup
    email = "test@example.com"
    code = "ABC123"
    
    # Mock HTTP client
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Replace client with our mock
    email_service_instance.client = mock_client
    
    # Execute
    result = await email_service_instance.send_activation_code(email, code)
    
    # Verify
    assert result is True
    mock_client.post.assert_called_once_with(
        email_service_instance.api_url,
        json={
            "to": email,
            "subject": "Your activation code",
            "body": f"Your activation code is: {code}"
        },
        timeout=10.0
    )
    print("✅ Email sent successfully")

@pytest.mark.asyncio
async def test_send_activation_code_without_client(email_service_instance):
    """
    Test when client is not initialized (uses default AsyncClient())
    Covers line 24 where we use 'self.client or httpx.AsyncClient()'
    """
    # Setup
    email = "test@example.com"
    code = "XYZ789"
    
    # Ensure client is None
    email_service_instance.client = None
    
    # Mock httpx.AsyncClient
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
        # Execute
        result = await email_service_instance.send_activation_code(email, code)
        
        # Verify
        assert result is True
        mock_client_class.assert_called_once()
        mock_client.post.assert_called_once()
        print("✅ Client automatically created and email sent")

@pytest.mark.asyncio
async def test_send_activation_code_http_error(email_service_instance):
    """
    Test when API returns an HTTP error
    Covers line 41 (return False on exception)
    """
    # Setup
    email = "test@example.com"
    code = "ERROR123"
    
    # Mock client that raises an exception
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
        "404 Not Found", 
        request=MagicMock(), 
        response=MagicMock(status_code=404)
    ))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    email_service_instance.client = mock_client
    
    # Execute
    result = await email_service_instance.send_activation_code(email, code)
    
    # Verify
    assert result is False
    mock_client.post.assert_called_once()
    print("✅ HTTP error properly handled (returns False)")

@pytest.mark.asyncio
async def test_send_activation_code_timeout_error(email_service_instance):
    """
    Test timeout error handling
    Covers line 41 (return False on exception)
    """
    # Setup
    email = "test@example.com"
    code = "TIMEOUT456"
    
    # Mock client that raises a timeout exception
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    email_service_instance.client = mock_client
    
    # Execute
    result = await email_service_instance.send_activation_code(email, code)
    
    # Verify
    assert result is False
    mock_client.post.assert_called_once()
    print("✅ Timeout properly handled (returns False)")

@pytest.mark.asyncio
async def test_send_activation_code_connection_error(email_service_instance):
    """
    Test connection error handling
    Covers line 41 (return False on exception)
    """
    # Setup
    email = "test@example.com"
    code = "CONN789"
    
    # Mock client that raises a connection error
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Failed to connect"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    email_service_instance.client = mock_client
    
    # Execute
    result = await email_service_instance.send_activation_code(email, code)
    
    # Verify
    assert result is False
    mock_client.post.assert_called_once()
    print("✅ Connection error properly handled (returns False)")

@pytest.mark.asyncio
async def test_send_activation_code_generic_exception(email_service_instance):
    """
    Test with a generic exception
    Covers line 41 (return False on exception)
    """
    # Setup
    email = "test@example.com"
    code = "GEN123"
    
    # Mock client that raises a generic exception
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post = AsyncMock(side_effect=Exception("Something went wrong"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    email_service_instance.client = mock_client
    
    # Execute
    result = await email_service_instance.send_activation_code(email, code)
    
    # Verify
    assert result is False
    mock_client.post.assert_called_once()
    print("✅ Generic exception properly handled (returns False)")

# Singleton test (optional)
def test_email_service_singleton():
    """
    Test that the singleton instance is of type EmailService
    """
    assert isinstance(email_service, EmailService)
    print("✅ Singleton instance available")