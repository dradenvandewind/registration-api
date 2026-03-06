from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.services.activation_service import ActivationService
from app.services.email_service import email_service
from app.core.exceptions import UserAlreadyExistsError

router = APIRouter(prefix="/registration", tags=["registration"])

def _validate_password(password: str) -> None:
    """
    Valide la longueur et la complexité du mot de passe.
    Lève une HTTPException 422 avec un message clair en cas d'échec.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Le mot de passe est trop court : "
                f"minimum {PASSWORD_MIN_LENGTH} caractères "
                f"(reçu : {len(password)})."
            ),
        )
    if len(password) > PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Le mot de passe est trop long : "
                f"maximum {PASSWORD_MAX_LENGTH} caractères "
                f"(reçu : {len(password)})."
            ),
        )



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
