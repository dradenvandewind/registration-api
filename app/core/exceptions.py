# app/core/exceptions.py
from fastapi import HTTPException, status

class UserAlreadyExistsError(Exception):
    """Exception raised when a user already exists"""
    pass

class UserNotFoundError(Exception):
    """Exception raised when a user is not found"""
    pass

class InvalidActivationCodeError(Exception):
    """Exception raised when the activation code is invalid or expired"""
    pass

class UserAlreadyActiveError(Exception):
    """Exception raised when the user is already active"""
    pass

# Function to set up FastAPI exception handlers
def setup_exception_handlers(app):
    """Configure exception handlers for the FastAPI application"""
    
    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(request, exc):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request, exc):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    @app.exception_handler(InvalidActivationCodeError)
    async def invalid_activation_code_handler(request, exc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired activation code"
        )
    
    @app.exception_handler(UserAlreadyActiveError)
    async def user_already_active_handler(request, exc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )