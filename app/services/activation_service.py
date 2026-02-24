from app.db.repositories.activation_repository import ActivationRepository
from app.db.repositories.user_repository import UserRepository
from app.models.activation import ActivationCodeCreate
from app.core.security import generate_activation_code
from app.core.config import settings
from app.core.exceptions import (
    InvalidActivationCodeError, 
    UserNotFoundError,
    UserAlreadyActiveError
)
from datetime import datetime, timedelta
from uuid import UUID

class ActivationService:
    def __init__(self):
        self.activation_repo = ActivationRepository()
        self.user_repo = UserRepository()

    async def create_activation_code(self, user_id: UUID) -> str:
        """Generate and store activation code"""
        # Invalidate previous codes
        await self.activation_repo.invalidate_old_codes(user_id)
        
        # Generate new code
        code = generate_activation_code()
        expires_at = datetime.utcnow() + timedelta(seconds=settings.activation_code_ttl_seconds)
        
        # Store in database
        activation_data = ActivationCodeCreate(
            user_id=user_id,
            code=code,
            expires_at=expires_at
        )
        
        await self.activation_repo.create(activation_data)
        return code

    async def activate_user(self, user_id: UUID, code: str) -> bool:
        """Activate user with code"""
        # Check if user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        
        # Check if already active
        if user.is_active:
            raise UserAlreadyActiveError("User is already active")
        
        # Validate code
        valid_code = await self.activation_repo.get_valid_code(user_id, code)
        if not valid_code:
            raise InvalidActivationCodeError("Invalid or expired activation code")
        
        # Mark code as used
        await self.activation_repo.mark_as_used(valid_code.id)
        
        # Activate user
        await self.user_repo.activate_user(user_id)
        
        return True
