from passlib.context import CryptContext
import secrets
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    # Bcrypt ne supporte que 72 bytes maximum
    # On tronque le mot de passe si nécessaire
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def generate_activation_code() -> str:
    """Generate a 4-digit code"""
    return ''.join(secrets.choice(string.digits) for _ in range(4))
