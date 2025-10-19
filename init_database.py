#!/usr/bin/env python3
"""
Script pour initialiser la base de données
Crée toutes les tables nécessaires
"""

import asyncio
import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Import de la base et de tous les modèles
from app.db.session import Base
from app.core.config import settings

# Import de tous les modèles pour qu'ils soient enregistrés
from app.models.user import User
from app.models.lot import Lot
from app.models.sale import Sale
from app.models.favorite import Favorite
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.price_history import PriceHistory
from app.models.comment import Comment

print("=" * 60)
print("INITIALISATION DE LA BASE DE DONNÉES")
print("=" * 60)
print()

async def init_database():
    """Initialize database tables"""

    print(f"📡 Connexion à la base de données...")
    print(f"   URL: {settings.DATABASE_URL}")
    print()

    try:
        # Créer le moteur
        engine = create_async_engine(settings.DATABASE_URL, echo=True)

        # Vérifier la connexion
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connexion réussie!")
            print(f"   PostgreSQL version: {version}")
            print()

        # Créer toutes les tables
        print("📦 Création des tables...")
        print()

        async with engine.begin() as conn:
            # Supprimer toutes les tables existantes (optionnel - décommentez si besoin)
            # await conn.run_sync(Base.metadata.drop_all)
            # print("⚠️  Tables existantes supprimées")

            # Créer toutes les tables
            await conn.run_sync(Base.metadata.create_all)
            print()
            print("✅ Tables créées avec succès!")

        # Vérifier les tables créées
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]

            print()
            print(f"📊 Tables créées ({len(tables)}):")
            for table in tables:
                print(f"   ✓ {table}")

        await engine.dispose()

        print()
        print("=" * 60)
        print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print()
        print("Prochaines étapes:")
        print("1. Redémarrez le backend: docker restart encheres_backend")
        print("2. Testez l'API: python3 test_api.py")
        print()

        return True

    except Exception as e:
        print()
        print("❌ ERREUR lors de l'initialisation:")
        print(f"   {str(e)}")
        print()
        print("Vérifications:")
        print("1. Le conteneur PostgreSQL est-il démarré?")
        print("   docker ps | grep encheres_db")
        print()
        print("2. Le port 5432 est-il accessible?")
        print("   nc -zv localhost 5432")
        print()
        return False

if __name__ == "__main__":
    result = asyncio.run(init_database())
    sys.exit(0 if result else 1)
