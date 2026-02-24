from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

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
