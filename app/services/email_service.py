import httpx
from app.core.config import settings
from typing import Optional

class EmailService:
    def __init__(self):
        self.api_url = settings.smtp_api_url
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def send_activation_code(self, email: str, code: str) -> bool:
        """
        Send activation code via third-party email service
        Mock implementation - in production this would call actual SMTP API
        """
        try:
            # Mock API call to email service
            # In production, this would be a real HTTP request
            print(f"📧 Sending activation code {code} to {email}")
            
            # Simulate API call
            async with self.client or httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={
                        "to": email,
                        "subject": "Your activation code",
                        "body": f"Your activation code is: {code}"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            # In production, we might want to retry or log to a dead letter queue
            return False

# Singleton instance
email_service = EmailService()
