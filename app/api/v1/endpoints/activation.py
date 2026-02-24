from fastapi import APIRouter, HTTPException, status, Depends
from app.models.activation import ActivationRequest, ActivationResponse
from app.services.activation_service import ActivationService
from app.dependencies.auth import get_current_user
from app.models.user import UserInDB
from app.core.exceptions import (
    InvalidActivationCodeError, 
    UserNotFoundError,
    UserAlreadyActiveError
)

router = APIRouter(prefix="/activation", tags=["activation"])

@router.post("", response_model=ActivationResponse)
async def activate_account(
    activation_data: ActivationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Activate user account with 4-digit code
    Requires Basic Auth with email and password
    """
    try:
        activation_service = ActivationService()
        
        await activation_service.activate_user(
            current_user.id,
            activation_data.code
        )
        
        return ActivationResponse(
            message="Account activated successfully",
            user_id=current_user.id
        )
        
    except (UserNotFoundError, UserAlreadyActiveError, InvalidActivationCodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
