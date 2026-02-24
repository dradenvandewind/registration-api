from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserResponse, UserInDB
from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from typing import Optional
from uuid import UUID

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        # Check if user already exists
        existing_user = await self.repository.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError("User with this email already exists")
        
        # Create user
        user = await self.repository.create(user_data)
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        return UserResponse.model_validate(user)

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
