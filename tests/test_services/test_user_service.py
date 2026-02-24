# tests/test_services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from app.services.user_service import UserService
from app.models.user import UserCreate, UserInDB, UserResponse
from app.core.exceptions import UserNotFoundError

@pytest.fixture
def user_service():
    """Fixture pour créer une instance du service avec repository mocké"""
    service = UserService()
    service.repository = AsyncMock()  # Mock du repository
    return service

@pytest.fixture
def sample_user_in_db():
    """Fixture pour un utilisateur tel qu'en base"""
    return UserInDB(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        is_active=False,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )

@pytest.mark.asyncio
async def test_get_user_success(user_service, sample_user_in_db):
    """
    Test de get_user quand l'utilisateur existe
    Couvre les lignes 36-39
    """
    # Configuration
    user_service.repository.get_by_id.return_value = sample_user_in_db
    
    # Exécution
    result = await user_service.get_user(sample_user_in_db.id)
    
    # Vérification
    assert isinstance(result, UserResponse)
    assert result.id == sample_user_in_db.id
    assert result.email == sample_user_in_db.email
    assert result.is_active == sample_user_in_db.is_active
    assert result.created_at == sample_user_in_db.created_at
    
    user_service.repository.get_by_id.assert_called_once_with(sample_user_in_db.id)
    print("✅ get_user - utilisateur trouvé retourne UserResponse")

@pytest.mark.asyncio
async def test_get_user_not_found(user_service):
    """
    Test de get_user quand l'utilisateur n'existe pas
    Couvre les lignes 37-39
    """
    # Configuration
    user_id = uuid4()
    user_service.repository.get_by_id.return_value = None
    
    # Exécution et vérification
    with pytest.raises(UserNotFoundError) as exc_info:
        await user_service.get_user(user_id)
    
    assert "User not found" in str(exc_info.value)
    user_service.repository.get_by_id.assert_called_once_with(user_id)
    print("✅ get_user - utilisateur inexistant lève UserNotFoundError")

@pytest.mark.asyncio
async def test_get_user_by_email_success(user_service, sample_user_in_db):
    """
    Test de get_user_by_email quand l'utilisateur existe
    Couvre les lignes 42-45
    """
    # Configuration
    email = "test@example.com"
    user_service.repository.get_by_email.return_value = sample_user_in_db
    
    # Exécution
    result = await user_service.get_user_by_email(email)
    
    # Vérification
    assert isinstance(result, UserInDB)
    assert result.email == email
    assert result.password_hash == "hashed_password"
    
    user_service.repository.get_by_email.assert_called_once_with(email)
    print("✅ get_user_by_email - utilisateur trouvé retourne UserInDB")

@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service):
    """
    Test de get_user_by_email quand l'utilisateur n'existe pas
    Couvre les lignes 43-45
    """
    # Configuration
    email = "nonexistent@example.com"
    user_service.repository.get_by_email.return_value = None
    
    # Exécution et vérification
    with pytest.raises(UserNotFoundError) as exc_info:
        await user_service.get_user_by_email(email)
    
    assert "User not found" in str(exc_info.value)
    user_service.repository.get_by_email.assert_called_once_with(email)
    print("✅ get_user_by_email - utilisateur inexistant lève UserNotFoundError")

@pytest.mark.asyncio
async def test_activate_user(user_service):
    """
    Test de activate_user
    Couvre la ligne 48
    """
    # Configuration
    user_id = uuid4()
    user_service.repository.activate_user = AsyncMock()
    
    # Exécution
    await user_service.activate_user(user_id)
    
    # Vérification
    user_service.repository.activate_user.assert_called_once_with(user_id)
    print("✅ activate_user - appel correct au repository")

@pytest.mark.asyncio
async def test_verify_credentials_success(user_service, sample_user_in_db):
    """
    Test de verify_credentials avec identifiants valides
    Couvre la ligne 58 (et le chemin de succès)
    """
    # Configuration
    email = "test@example.com"
    password = "correct_password"
    sample_user_in_db.password_hash = "$2b$12$hashed_password"  # Hash valide
    
    user_service.repository.get_by_email.return_value = sample_user_in_db
    
    # ✅ Mock à la source dans core.security
    with patch('app.core.security.verify_password', return_value=True) as mock_verify:
        # Exécution
        result = await user_service.verify_credentials(email, password)
        
        # Vérification
        assert result == sample_user_in_db
        user_service.repository.get_by_email.assert_called_once_with(email)
        mock_verify.assert_called_once_with(password, sample_user_in_db.password_hash)
        print("✅ verify_credentials - identifiants valides retourne l'utilisateur")

@pytest.mark.asyncio
async def test_verify_credentials_user_not_found(user_service):
    """
    Test de verify_credentials quand l'utilisateur n'existe pas
    Couvre le chemin alternatif de la ligne 58
    """
    # Configuration
    email = "unknown@example.com"
    password = "any_password"
    user_service.repository.get_by_email.return_value = None
    
    # Exécution
    result = await user_service.verify_credentials(email, password)
    
    # Vérification
    assert result is None
    user_service.repository.get_by_email.assert_called_once_with(email)
    print("✅ verify_credentials - utilisateur inexistant retourne None")

@pytest.mark.asyncio
async def test_verify_credentials_wrong_password(user_service, sample_user_in_db):
    """
    Test de verify_credentials avec mauvais mot de passe
    Couvre le chemin alternatif de la ligne 58
    """
    # Configuration
    email = "test@example.com"
    wrong_password = "wrong_password"
    user_service.repository.get_by_email.return_value = sample_user_in_db
    
    # Mock de verify_password à la source (dans core.security)
    with patch('app.core.security.verify_password', return_value=False) as mock_verify:
        # Exécution
        result = await user_service.verify_credentials(email, wrong_password)
        
        # Vérification
        assert result is None
        user_service.repository.get_by_email.assert_called_once_with(email)
        mock_verify.assert_called_once_with(wrong_password, sample_user_in_db.password_hash)
        print("✅ verify_credentials - mauvais mot de passe retourne None")