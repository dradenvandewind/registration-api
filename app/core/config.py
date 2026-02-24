from pydantic_settings import SettingsConfigDict, BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@db:5432/registration_db"
    
    # Redis
    redis_url: str = "redis://redis:6379"
    
    # Security
    secret_key: str = "dev_secret_key_change_in_production"
    bcrypt_rounds: int = 12
    
    # Email
    smtp_api_url: str = "http://mailhog:8025/api/v1/send"

    @property
    def database_url(self) -> str:
        """Retourne l'URL de la base de données selon l'environnement"""
        if os.getenv("ENVIRONMENT") == "test":
            return os.getenv("TEST_DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")
        return os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/main_db")
    
    # Activation
    activation_code_ttl_seconds: int = 60  # 1 minute
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
