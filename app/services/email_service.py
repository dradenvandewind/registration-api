import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
from app.core.config import settings
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        parsed = urlparse(settings.smtp_api_url)
        self.smtp_host = parsed.hostname or "mailhog"
        self.smtp_port = parsed.port or 1025

    async def send_activation_code(self, email: str, code: str) -> bool:
        """
        Envoie le code d'activation par SMTP (MailHog en dev).
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your activation code"
            msg["From"] = "noreply@registration-api.local"
            msg["To"] = email

            body = MIMEText(
                f"Your activation code is: {code}\n\nThis code expires in 1 hour.",
                "plain"
            )
            msg.attach(body)

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.sendmail(msg["From"], [email], msg.as_string())

            logger.info(f"Activation email sent to {email} (code: {code})")
            return True

        except Exception as e:
            logger.error(f"Failed to send activation email to {email}: {e}")
            return False


# Singleton instance
email_service = EmailService()