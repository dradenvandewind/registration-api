from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.services.user_service import UserService
from app.core.exceptions import UserNotFoundError

security = HTTPBasic()

async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security)
):
    """Dependency to get current authenticated user"""
    user_service = UserService()
    
    try:
        user = await user_service.verify_credentials(
            credentials.username, 
            credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        return user
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
