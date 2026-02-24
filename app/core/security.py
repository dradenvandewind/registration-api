# app/core/security.py
#from passlib.context import CryptContext
import secrets
import string
import logging
from typing import Optional
import bcrypt

logger = logging.getLogger(__name__)


class PasswordHandler:
    """Password hash manager using bcrypt directly"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with bcrypt"""
        try:
            # Convert to bytes and ensure 72 bytes limit
            password_bytes = password.encode('utf-8')
            
            # Explicit truncation if necessary (optional, depending on your policy)
            if len(password_bytes) > 72:
                logger.warning("Password too long, truncating to 72 bytes")
                password_bytes = password_bytes[:72]
            
            # Generate salt and hash
            salt = bcrypt.gensalt(rounds=12)  # 12 rounds is a good compromise
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Return hash as string
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Check if password matches the hash"""
        try:
            # Prepare bytes
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Verify
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

# Singleton instance
password_handler = PasswordHandler()

# Functions to maintain compatibility with existing code
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_handler.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_handler.hash_password(password)

def generate_activation_code(length: int = 6) -> str:
    """
    Generate a random activation code.
    
    Args:
        length: Code length (default: 6)
    
    Returns:
        A random alphanumeric code
    """
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    logger.info(f"Activation code generated: {code}")
    return code