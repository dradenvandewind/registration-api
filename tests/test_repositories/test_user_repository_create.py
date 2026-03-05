# tests/test_repositories/test_user_repository_create.py
"""
Tests pour UserRepository.create et get_by_email.
Ces méthodes ne sont pas couvertes dans la suite existante.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.db.repositories.user_repository import UserRepository
from app.models.user import UserCreate, UserInDB


@pytest.fixture
def user_repository():
    return UserRepository()


@pytest.fixture
def sample_user_create():
    return UserCreate(email="new@example.com", password="securepass123")


@pytest.fixture
def mock_user_dict():
    now = datetime.utcnow()
    return {
        "id": uuid4(),
        "email": "new@example.com",
        "password_hash": "$2b$12$somehash",
        "is_active": False,
        "created_at": now,
        "updated_at": now,
    }


@pytest.fixture
def mock_row(mock_user_dict):
    class MockRow:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def keys(self):
            return self._data.keys()

        def items(self):
            return self._data.items()

        def __iter__(self):
            return iter(self._data)

    return MockRow(mock_user_dict)


# ---------------------------------------------------------------------------
# UserRepository.create
# ---------------------------------------------------------------------------

class TestUserRepositoryCreate:
    """Tests pour la méthode create (lignes 10-17)."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, sample_user_create, mock_row, mock_user_dict):
        """
        Chemin nominal : hash du mot de passe puis INSERT en base.
        """
        with patch("app.db.repositories.user_repository.get_password_hash") as mock_hash, \
             patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock) as mock_fetchrow:

            mock_hash.return_value = "$2b$12$somehash"
            mock_fetchrow.return_value = mock_row

            result = await user_repository.create(sample_user_create)

            assert isinstance(result, UserInDB)
            assert result.email == mock_user_dict["email"]
            assert result.password_hash == "$2b$12$somehash"
            assert result.is_active is False

            mock_hash.assert_called_once_with(sample_user_create.password)
            mock_fetchrow.assert_called_once()

            # La requête doit contenir INSERT INTO users
            query = mock_fetchrow.call_args[0][0]
            assert "INSERT INTO users" in query
            assert "$1" in query and "$2" in query
            print("✅ UserRepository.create - chemin nominal")

    @pytest.mark.asyncio
    async def test_create_hashes_password_before_insert(self, user_repository, sample_user_create, mock_row):
        """
        Le mot de passe clair ne doit jamais être passé à fetchrow ; seul le hash l'est.
        """
        hashed = "$2b$12$xyzHASH"
        with patch("app.db.repositories.user_repository.get_password_hash", return_value=hashed), \
             patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock, return_value=mock_row) as mock_fetchrow:

            await user_repository.create(sample_user_create)

            call_args = mock_fetchrow.call_args[0]
            # call_args[1] = email, call_args[2] = password_hash
            assert call_args[2] == hashed
            assert call_args[2] != sample_user_create.password
            print("✅ UserRepository.create - le hash (pas le mdp clair) est envoyé en base")

    @pytest.mark.asyncio
    async def test_create_db_error_propagates(self, user_repository, sample_user_create):
        """
        Une erreur DB doit remonter telle quelle.
        """
        with patch("app.db.repositories.user_repository.get_password_hash", return_value="hash"), \
             patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock,
                   side_effect=Exception("Unique violation")):

            with pytest.raises(Exception) as exc_info:
                await user_repository.create(sample_user_create)

            assert "Unique violation" in str(exc_info.value)
            print("✅ UserRepository.create - erreur DB propagée")


# ---------------------------------------------------------------------------
# UserRepository.get_by_email
# ---------------------------------------------------------------------------

class TestUserRepositoryGetByEmail:
    """Tests pour get_by_email (lignes 19-22)."""

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, user_repository, mock_row, mock_user_dict):
        """Retourne un UserInDB quand l'email existe."""
        with patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock) as mock_fetchrow:
            mock_fetchrow.return_value = mock_row

            result = await user_repository.get_by_email("new@example.com")

            assert isinstance(result, UserInDB)
            assert result.email == mock_user_dict["email"]

            query = mock_fetchrow.call_args[0][0]
            assert "WHERE email = $1" in query
            print("✅ UserRepository.get_by_email - utilisateur trouvé")

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """Retourne None quand l'email n'existe pas."""
        with patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock,
                   return_value=None):

            result = await user_repository.get_by_email("ghost@example.com")

            assert result is None
            print("✅ UserRepository.get_by_email - utilisateur non trouvé retourne None")

    @pytest.mark.asyncio
    async def test_get_by_email_db_error_propagates(self, user_repository):
        """Une erreur DB doit remonter."""
        with patch("app.db.repositories.user_repository.db.fetchrow", new_callable=AsyncMock,
                   side_effect=Exception("Connection lost")):

            with pytest.raises(Exception) as exc_info:
                await user_repository.get_by_email("test@example.com")

            assert "Connection lost" in str(exc_info.value)
            print("✅ UserRepository.get_by_email - erreur DB propagée")