from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.services.activation_service import ActivationService
from app.services.email_service import email_service
from app.core.exceptions import UserAlreadyExistsError

router = APIRouter(prefix="/registration", tags=["registration"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks
):
    """
    Register a new user with email and password
    An activation code will be sent via email
    """
    try:
        # Create user
        user_service = UserService()
        user = await user_service.create_user(user_data)
        
        # Generate activation code
        activation_service = ActivationService()
        code = await activation_service.create_activation_code(user.id)
        
        # Send email with code (background task)
        background_tasks.add_task(
            email_service.send_activation_code,
            user.email,
            code
        )
        
        return user
        
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
