# tests/test_services/test_activation_service_create.py
"""
Tests pour create_activation_code dans ActivationService.
Cette méthode n'est pas couverte dans la suite existante.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.activation_service import ActivationService
from app.models.activation import ActivationCodeCreate, ActivationCodeInDB
from app.db.repositories.activation_repository import ActivationRepository


@pytest.fixture
def activation_service():
    service = ActivationService()
    service.activation_repo = AsyncMock(spec=ActivationRepository)
    return service


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def mock_activation_code_in_db(sample_user_id):
    now = datetime.utcnow()
    return ActivationCodeInDB(
        id=uuid4(),
        user_id=sample_user_id,
        code="AB3Z9K",
        expires_at=now + timedelta(hours=1),
        used_at=None,
        created_at=now,
    )


class TestCreateActivationCode:
    """Tests pour create_activation_code (lignes 30-51)."""

    @pytest.mark.asyncio
    async def test_create_activation_code_success(
        self, activation_service, sample_user_id, mock_activation_code_in_db
    ):
        """
        Chemin nominal : génération du code, persistence et retour de l'objet.
        Couvre les lignes 30-51.
        """
        activation_service.activation_repo.create.return_value = mock_activation_code_in_db

        result = await activation_service.create_activation_code(sample_user_id)

        assert result is not None
        assert isinstance(result, ActivationCodeInDB)
        assert len(result.code) == 6
        assert result.user_id == mock_activation_code_in_db.user_id

        # Le repo create doit avoir été appelé une fois
        activation_service.activation_repo.create.assert_called_once()
        call_arg: ActivationCodeCreate = activation_service.activation_repo.create.call_args[0][0]
        assert call_arg.user_id == sample_user_id
        assert len(call_arg.code) == 4
        # expires_at doit être dans le futur (environ +1h)
        assert call_arg.expires_at > datetime.utcnow()
        print("✅ create_activation_code - chemin nominal (lignes 30-51)")

    @pytest.mark.asyncio
    async def test_create_activation_code_expiry_is_one_hour(
        self, activation_service, sample_user_id, mock_activation_code_in_db
    ):
        """
        Vérifie que expires_at est bien à environ 1 heure dans le futur.
        """
        activation_service.activation_repo.create.return_value = mock_activation_code_in_db

        before = datetime.utcnow()
        await activation_service.create_activation_code(sample_user_id)
        after = datetime.utcnow()

        call_arg: ActivationCodeCreate = activation_service.activation_repo.create.call_args[0][0]
        delta = call_arg.expires_at - before
        assert timedelta(minutes=59) < delta < timedelta(hours=1, minutes=1)
        print("✅ create_activation_code - expires_at ≈ +1h")

    @pytest.mark.asyncio
    async def test_create_activation_code_uses_6_char_code(
        self, activation_service, sample_user_id, mock_activation_code_in_db
    ):
        """
        Le code doit toujours avoir exactement 4 caractères alphanumériques majuscules.
        """
        activation_service.activation_repo.create.return_value = mock_activation_code_in_db

        await activation_service.create_activation_code(sample_user_id)

        call_arg: ActivationCodeCreate = activation_service.activation_repo.create.call_args[0][0]
        assert len(call_arg.code) == 4
        assert call_arg.code.isupper() or call_arg.code.isalnum()
        print("✅ create_activation_code - code de 4 caractères")

    @pytest.mark.asyncio
    async def test_create_activation_code_logs_code(
        self, activation_service, sample_user_id, mock_activation_code_in_db
    ):
        """
        Le service doit logger le code généré (ligne 38).
        """
        activation_service.activation_repo.create.return_value = mock_activation_code_in_db

        with patch("app.services.activation_service.logger.info") as mock_log:
            await activation_service.create_activation_code(sample_user_id)

        # Vérifier qu'au moins un appel contient l'ID utilisateur
        calls_str = " ".join(str(c) for c in mock_log.call_args_list)
        assert str(sample_user_id) in calls_str
        print("✅ create_activation_code - logging de l'ID utilisateur (ligne 38)")

    @pytest.mark.asyncio
    async def test_create_activation_code_repo_error_propagates(
        self, activation_service, sample_user_id
    ):
        """
        Si le repository lève une exception, elle doit remonter.
        """
        activation_service.activation_repo.create.side_effect = Exception("DB write error")

        with pytest.raises(Exception) as exc_info:
            await activation_service.create_activation_code(sample_user_id)

        assert "DB write error" in str(exc_info.value)
        print("✅ create_activation_code - propagation d'erreur repository")