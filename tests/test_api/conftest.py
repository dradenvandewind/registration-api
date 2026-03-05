# tests/test_api/conftest.py
"""
Fixtures locales aux tests API.
On patche directement les méthodes du singleton `db` avec patch.object
pour contourner le check `if not self.pool` sans avoir besoin de Docker.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from app.db.connection import db  # le singleton réel


# ---------------------------------------------------------------------------
# Helpers publics (utilisables dans les tests)
# ---------------------------------------------------------------------------

def make_user_row(email: str, is_active: bool = False, user_id=None):
    now = datetime.utcnow()

    class FakeRow:
        _d = {
            "id": user_id or uuid4(),
            "email": email,
            "password_hash": "$2b$12$fakehash",
            "is_active": is_active,
            "created_at": now,
            "updated_at": now,
        }
        def __getitem__(self, k): return self._d[k]
        def keys(self): return self._d.keys()
        def items(self): return self._d.items()
        def __iter__(self): return iter(self._d)

    return FakeRow()


def make_code_row(user_id, code: str):
    now = datetime.utcnow()

    class FakeRow:
        _d = {
            "id": uuid4(),
            "user_id": user_id,
            "code": code,
            "expires_at": now + timedelta(hours=1),
            "used_at": None,
            "created_at": now,
        }
        def __getitem__(self, k): return self._d[k]
        def keys(self): return self._d.keys()
        def items(self): return self._d.items()
        def __iter__(self): return iter(self._d)

    return FakeRow()


# ---------------------------------------------------------------------------
# Fixture principale
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_db_pool():
    """
    Patche fetchrow / fetch / execute directement sur le singleton `db`.
    Contourne le check `if not self.pool` sans manipuler le pool asyncpg.

    Valeurs par défaut :
      - fetchrow → None
      - fetch    → []
      - execute  → "OK"

    Les tests reçoivent un objet DbMocks et peuvent faire :
        mock_db_pool.fetchrow.side_effect = [row1, row2]
    """
    mock_fetchrow = AsyncMock(return_value=None)
    mock_fetch    = AsyncMock(return_value=[])
    mock_execute  = AsyncMock(return_value="OK")

    with patch.object(db, "fetchrow", mock_fetchrow), \
         patch.object(db, "fetch",    mock_fetch), \
         patch.object(db, "execute",  mock_execute):

        class DbMocks:
            fetchrow = mock_fetchrow
            fetch    = mock_fetch
            execute  = mock_execute

        yield DbMocks()