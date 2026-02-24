from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ActivationCodeCreate(BaseModel):
    user_id: UUID
    code: str
    expires_at: datetime

class ActivationCodeInDB(BaseModel):
    id: UUID
    user_id: UUID
    code: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime

class ActivationRequest(BaseModel):
    code: str  # Validation faite dans le endpoint

class ActivationResponse(BaseModel):
    message: str
    user_id: UUID
