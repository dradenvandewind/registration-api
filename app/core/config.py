from pydantic_settings import BaseSettings
from typing import Optional

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
    
    # Activation
    activation_code_ttl_seconds: int = 60  # 1 minute
    
    class Config:
        env_file = ".env"

settings = Settings()
