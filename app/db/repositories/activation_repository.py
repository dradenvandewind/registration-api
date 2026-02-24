from app.db.connection import db
from app.models.activation import ActivationCodeInDB, ActivationCodeCreate
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

class ActivationRepository:
    async def create(self, activation_data: ActivationCodeCreate) -> ActivationCodeInDB:
        query = """
            INSERT INTO activation_codes (user_id, code, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, code, expires_at, used_at, created_at
        """
        row = await db.fetchrow(
            query, 
            activation_data.user_id, 
            activation_data.code, 
            activation_data.expires_at
        )
        return ActivationCodeInDB(**dict(row))

    async def get_valid_code(self, user_id: UUID, code: str) -> Optional[ActivationCodeInDB]:
        query = """
            SELECT * FROM activation_codes 
            WHERE user_id = $1 
            AND code = $2 
            AND used_at IS NULL 
            AND expires_at > CURRENT_TIMESTAMP
            ORDER BY created_at DESC 
            LIMIT 1
        """
        row = await db.fetchrow(query, user_id, code)
        return ActivationCodeInDB(**dict(row)) if row else None

    async def mark_as_used(self, code_id: UUID) -> None:
        query = "UPDATE activation_codes SET used_at = CURRENT_TIMESTAMP WHERE id = $1"
        await db.execute(query, code_id)

    async def invalidate_old_codes(self, user_id: UUID) -> None:
        """Mark all previous codes as used"""
        query = """
            UPDATE activation_codes 
            SET used_at = CURRENT_TIMESTAMP 
            WHERE user_id = $1 AND used_at IS NULL
        """
        await db.execute(query, user_id)
