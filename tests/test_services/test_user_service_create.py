# tests/test_services/test_user_service_create.py
"""
Tests pour UserService.create_user.
Non couverts dans la suite existante.
"""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.user_service import UserService
from app.models.user import UserCreate, UserInDB, UserResponse
from app.core.exceptions import UserAlreadyExistsError
from app.db.repositories.user_repository import UserRepository


@pytest.fixture
def user_service():
    service = UserService()
    service.repository = AsyncMock(spec=UserRepository)
    return service


@pytest.fixture
def user_create_data():
    return UserCreate(email="alice@example.com", password="s123")


@pytest.fixture
def existing_user_in_db():
    now = datetime.utcnow()
    return UserInDB(
        id=uuid4(),
        email="alice@example.com",
        password_hash="$2b$12$hash",
        is_active=False,
        created_at=now,
        updated_at=now,
    )


class TestUserServiceCreateUser:
    """Tests pour create_user (lignes 10-24 de user_service.py)."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, user_create_data, existing_user_in_db):
        """
        Chemin nominal : email non utilisé → création OK → retour UserResponse.
        """
        user_service.repository.get_by_email.return_value = None
        user_service.repository.create.return_value = existing_user_in_db

        result = await user_service.create_user(user_create_data)

        assert isinstance(result, UserResponse)
        assert result.email == user_create_data.email
        assert result.is_active is False
        assert result.id == existing_user_in_db.id

        user_service.repository.get_by_email.assert_called_once_with(user_create_data.email)
        user_service.repository.create.assert_called_once_with(user_create_data)
        print("✅ UserService.create_user - chemin nominal")

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises(self, user_service, user_create_data, existing_user_in_db):
        """
        Si l'email existe déjà, UserAlreadyExistsError doit être levée.
        """
        user_service.repository.get_by_email.return_value = existing_user_in_db

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_service.create_user(user_create_data)

        assert "already exists" in str(exc_info.value).lower()
        # Le repository ne doit pas essayer de créer
        user_service.repository.create.assert_not_called()
        print("✅ UserService.create_user - email dupliqué lève UserAlreadyExistsError")

    @pytest.mark.asyncio
    async def test_create_user_response_does_not_expose_password_hash(
        self, user_service, user_create_data, existing_user_in_db
    ):
        """
        Le UserResponse retourné ne doit pas contenir password_hash.
        """
        user_service.repository.get_by_email.return_value = None
        user_service.repository.create.return_value = existing_user_in_db

        result = await user_service.create_user(user_create_data)

        assert not hasattr(result, "password_hash")
        print("✅ UserService.create_user - password_hash absent du UserResponse")

    @pytest.mark.asyncio
    async def test_create_user_repo_create_error_propagates(self, user_service, user_create_data):
        """
        Une erreur du repository lors du create doit remonter.
        """
        user_service.repository.get_by_email.return_value = None
        user_service.repository.create.side_effect = Exception("DB insert error")

        with pytest.raises(Exception) as exc_info:
            await user_service.create_user(user_create_data)

        assert "DB insert error" in str(exc_info.value)
        print("✅ UserService.create_user - erreur repository propagée")

    @pytest.mark.asyncio
    async def test_create_user_new_user_is_inactive(self, user_service, user_create_data, existing_user_in_db):
        """
        Un utilisateur nouvellement créé doit avoir is_active = False.
        """
        user_service.repository.get_by_email.return_value = None
        user_service.repository.create.return_value = existing_user_in_db

        result = await user_service.create_user(user_create_data)

        assert result.is_active is False
        print("✅ UserService.create_user - is_active=False pour un nouvel utilisateur")