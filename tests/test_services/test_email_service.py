import pytest
from unittest.mock import MagicMock
import smtplib

from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_send_activation_code_success(monkeypatch):
    """
    Check that the email is sent correctly if SMTP is working.
    """

    mock_server = MagicMock()

    class MockSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            return mock_server

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)

    service = EmailService()

    result = await service.send_activation_code("test@example.com", "123456")

    assert result is True
    mock_server.sendmail.assert_called_once()
    
@pytest.mark.asyncio
async def test_send_activation_code_failure(monkeypatch):
    """
    Checks that False is returned if SMTP fails
    """

    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            raise smtplib.SMTPException("SMTP error")

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)

    service = EmailService()

    result = await service.send_activation_code("test@example.com", "123456")

    assert result is False
    
@pytest.mark.asyncio
async def test_email_content(monkeypatch):
    """
    Check that the email content contains the code
    """

    captured_message = {}

    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def sendmail(self, sender, recipients, message):
            captured_message["sender"] = sender
            captured_message["recipients"] = recipients
            captured_message["message"] = message

    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)

    service = EmailService()

    await service.send_activation_code("user@test.com", "999999")

    assert captured_message["sender"] == "noreply@registration-api.local"
    assert "999999" in captured_message["message"]
    assert "user@test.com" in captured_message["recipients"]

def test_smtp_host_parsing(monkeypatch):
    """
    Verify that the SMTP host is correctly extracted from the URL.
    """

    class MockSettings:
        smtp_api_url = "smtp://mailhog:1025"

    monkeypatch.setattr(
        "app.services.email_service.settings",
        MockSettings
    )

    service = EmailService()

    assert service.smtp_host == "mailhog"
    assert service.smtp_port == 1025