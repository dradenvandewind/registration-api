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
        """Check that the password contains at least one letter and one number.."""
        if not any(c.isdigit() for c in v):
            raise ValueError("The password must contain at least one number.")
        if not any(c.isalpha() for c in v):
            raise ValueError("The password must contain at least one letter.")
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