import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.connection import db
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Initialise la base de données pour les tests"""
    print("\n" + "="*50)
    print("🔄 Initialisation de la base de données de test...")
    print("="*50)
    
    # Initialiser la connexion
    await db.initialize()
    
    # Vérifier que la connexion est établie
    if db.pool is None:
        print("❌ Échec de l'initialisation de la base de données")
        raise Exception("Database pool is None after initialization")
    
    print(f"✅ Base de données connectée")
    
    # Nettoyer les tables
    try:
        await db.execute("DELETE FROM activation_codes")
        await db.execute("DELETE FROM users")
        print("✅ Tables nettoyées")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")
    
    yield
    
    # Fermer la connexion à la fin des tests
    print("\n" + "="*50)
    print("🔄 Fermeture de la connexion à la base de données...")
    print("="*50)
    await db.close()
    print("✅ Connexion fermée")

@pytest.fixture(scope="function", autouse=True)
async def clean_db_between_tests():
    """Nettoie la base de données entre chaque test"""
    yield
    try:
        await db.execute("DELETE FROM activation_codes")
        await db.execute("DELETE FROM users")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage entre tests: {e}")
