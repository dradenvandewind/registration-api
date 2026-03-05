# tests/test_repositories/test_activation_repository_create.py
"""
Tests pour ActivationRepository.create.
Non couverts dans la suite existante.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.db.repositories.activation_repository import ActivationRepository
from app.models.activation import ActivationCodeCreate, ActivationCodeInDB


@pytest.fixture
def activation_repository():
    return ActivationRepository()


@pytest.fixture
def sample_activation_create():
    return ActivationCodeCreate(
        user_id=uuid4(),
        code="XY7K2P",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )


@pytest.fixture
def mock_activation_dict(sample_activation_create):
    now = datetime.utcnow()
    return {
        "id": uuid4(),
        "user_id": sample_activation_create.user_id,
        "code": sample_activation_create.code,
        "expires_at": sample_activation_create.expires_at,
        "used_at": None,
        "created_at": now,
    }


@pytest.fixture
def mock_row(mock_activation_dict):
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

    return MockRow(mock_activation_dict)


class TestActivationRepositoryCreate:
    """Tests pour ActivationRepository.create (lignes 10-19)."""

    @pytest.mark.asyncio
    async def test_create_success(self, activation_repository, sample_activation_create, mock_row, mock_activation_dict):
        """Chemin nominal : INSERT puis retour d'un ActivationCodeInDB."""
        with patch("app.db.repositories.activation_repository.db.fetchrow",
                   new_callable=AsyncMock, return_value=mock_row) as mock_fetchrow:

            result = await activation_repository.create(sample_activation_create)

            assert isinstance(result, ActivationCodeInDB)
            assert result.code == mock_activation_dict["code"]
            assert result.user_id == mock_activation_dict["user_id"]
            assert result.used_at is None

            query = mock_fetchrow.call_args[0][0]
            assert "INSERT INTO activation_codes" in query
            assert "RETURNING" in query
            print("✅ ActivationRepository.create - chemin nominal")

    @pytest.mark.asyncio
    async def test_create_passes_correct_args(self, activation_repository, sample_activation_create, mock_row):
        """Les arguments user_id, code et expires_at doivent être passés dans le bon ordre."""
        with patch("app.db.repositories.activation_repository.db.fetchrow",
                   new_callable=AsyncMock, return_value=mock_row) as mock_fetchrow:

            await activation_repository.create(sample_activation_create)

            args = mock_fetchrow.call_args[0]
            # args[0] = query, args[1] = user_id, args[2] = code, args[3] = expires_at
            assert args[1] == sample_activation_create.user_id
            assert args[2] == sample_activation_create.code
            assert args[3] == sample_activation_create.expires_at
            print("✅ ActivationRepository.create - bons paramètres passés à fetchrow")

    @pytest.mark.asyncio
    async def test_create_db_error_propagates(self, activation_repository, sample_activation_create):
        """Une erreur DB doit remonter telle quelle."""
        with patch("app.db.repositories.activation_repository.db.fetchrow",
                   new_callable=AsyncMock, side_effect=Exception("Constraint violation")):

            with pytest.raises(Exception) as exc_info:
                await activation_repository.create(sample_activation_create)

            assert "Constraint violation" in str(exc_info.value)
            print("✅ ActivationRepository.create - erreur DB propagée")