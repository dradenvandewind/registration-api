from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional

PASSWORD_MIN_LENGTH = 4
PASSWORD_MAX_LENGTH = 4 


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """Vérifie que le mot de passe contient au moins une lettre et un chiffre."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        if not any(c.isalpha() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une lettre.")
        return v


class UserInDB(BaseModel):
    id: UUID
    email: EmailStr
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime