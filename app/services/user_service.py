from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserResponse, UserInDB
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from typing import Optional
from uuid import UUID

import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        # Vérifier si l'utilisateur existe déjà
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError("User with this email already exists")
        
        # Créer l'utilisateur
        user_in_db = await self.repository.create(user_data)
        logger.info(f"Utilisateur créé en base: {user_in_db}")
        
        # SOLUTION: Créer manuellement le UserResponse
        user_response = UserResponse(
            id=user_in_db.id,
            email=user_in_db.email,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at
        )
        
        return user_response

    async def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        # ✅ Conversion manuelle (comme dans create_user)
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
        return user_response

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        user = await self.repository.get_by_email(email)
        if not user:
            raise UserNotFoundError("User not found")
        return user

    async def activate_user(self, user_id: UUID) -> None:
        await self.repository.activate_user(user_id)

    async def verify_credentials(self, email: str, password: str) -> Optional[UserInDB]:
        from app.core.security import verify_password
        
        user = await self.repository.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
