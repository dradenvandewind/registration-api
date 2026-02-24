from app.db.connection import db
from app.models.user import UserInDB, UserCreate
from app.core.security import get_password_hash
from typing import Optional
from uuid import UUID

class UserRepository:
    async def create(self, user_data: UserCreate) -> UserInDB:
        password_hash = get_password_hash(user_data.password)
        query = """
            INSERT INTO users (email, password_hash)
            VALUES ($1, $2)
            RETURNING id, email, password_hash, is_active, created_at, updated_at
        """
        row = await db.fetchrow(query, user_data.email, password_hash)
        return UserInDB(**dict(row))

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        query = "SELECT * FROM users WHERE email = $1"
        row = await db.fetchrow(query, email)
        return UserInDB(**dict(row)) if row else None

    async def get_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        query = "SELECT * FROM users WHERE id = $1"
        row = await db.fetchrow(query, user_id)
        return UserInDB(**dict(row)) if row else None

    async def activate_user(self, user_id: UUID) -> None:
        query = "UPDATE users SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = $1"
        await db.execute(query, user_id)

    async def update_password(self, user_id: UUID, new_password: str) -> None:
        password_hash = get_password_hash(new_password)
        query = "UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2"
        await db.execute(query, password_hash, user_id)
