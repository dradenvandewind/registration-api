#from passlib.context import CryptContext
import secrets
import string
import logging
from typing import Optional
import bcrypt

logger = logging.getLogger(__name__)

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Vérifie si le mot de passe correspond au hash"""
#     try:
#         return pwd_context.verify(plain_password, hashed_password)
#     except Exception as e:
#         logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
#         return False

# def get_password_hash(password: str) -> str:
#     """Génère un hash du mot de passe"""
#     try:
#         # S'assurer que le mot de passe n'est pas trop long
#         if len(password.encode('utf-8')) > 72:
#             logger.warning("Mot de passe trop long, troncature automatique")
#             password = password[:72]  # Troncature si nécessaire
#         return pwd_context.hash(password)
#     except Exception as e:
#         logger.error(f"Erreur lors du hash du mot de passe: {e}")
#         raise

# def generate_activation_code() -> str:
#     """Generate a 4-digit code"""
#     return ''.join(secrets.choice(string.digits) for _ in range(4))
class PasswordHandler:
    """Gestionnaire de hash de mots de passe avec bcrypt directement"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt"""
        try:
            # Convertir en bytes et s'assurer de la limite de 72 bytes
            password_bytes = password.encode('utf-8')
            
            # Troncature explicite si nécessaire (optionnel, selon votre politique)
            if len(password_bytes) > 72:
                logger.warning("Mot de passe trop long, troncature à 72 bytes")
                password_bytes = password_bytes[:72]
            
            # Générer le salt et hasher
            salt = bcrypt.gensalt(rounds=12)  # 12 rounds est un bon compromis
            hashed = bcrypt.hashpw(password_bytes, salt)
            
            # Retourner le hash en string
            return hashed.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erreur lors du hash du mot de passe: {e}")
            raise
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Vérifie si le mot de passe correspond au hash"""
        try:
            # Préparer les bytes
            plain_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            # Vérifier
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return False

# Instance unique
password_handler = PasswordHandler()

# Fonctions pour garder la compatibilité avec le code existant
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_handler.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_handler.hash_password(password)

def generate_activation_code(length: int = 6) -> str:
    """
    Génère un code d'activation aléatoire.
    
    Args:
        length: Longueur du code (défaut: 6)
    
    Returns:
        Un code alphanumérique aléatoire
    """
    alphabet = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(length))
    logger.info(f"Code d'activation généré: {code}")
    return code