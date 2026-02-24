import asyncpg
from typing import Optional
from app.core.config import settings

class DatabasePool:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False

    async def initialize(self):
        """Initialise le pool de connexions"""
        if self._initialized:
            return
            
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self._initialized = True
            print(f"✅ Pool de connexions initialisé: {settings.database_url}")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du pool: {e}")
            raise

    async def close(self):
        """Ferme le pool de connexions"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            print("✅ Pool de connexions fermé")

    async def execute(self, query: str, *args):
        """Exécute une requête sans retour de résultat"""
        if not self.pool:
            raise RuntimeError("Base de données non initialisée. Appelez initialize() d'abord.")
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Récupère plusieurs lignes"""
        if not self.pool:
            raise RuntimeError("Base de données non initialisée. Appelez initialize() d'abord.")
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Récupère une seule ligne"""
        if not self.pool:
            raise RuntimeError("Base de données non initialisée. Appelez initialize() d'abord.")
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

db = DatabasePool()