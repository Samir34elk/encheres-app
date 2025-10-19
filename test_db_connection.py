#!/usr/bin/env python3
"""
Script pour tester la connexion à la base de données
"""

import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

# URL de la base de données
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/encheres"

async def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("TEST DE CONNEXION À LA BASE DE DONNÉES")
    print("=" * 60)
    print()

    try:
        print(f"📡 Tentative de connexion à: {DATABASE_URL}")
        engine = create_async_engine(DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            # Test simple query
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connexion réussie!")
            print(f"   PostgreSQL version: {version}")
            print()

            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]

            if tables:
                print(f"✅ Tables trouvées ({len(tables)}):")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  Aucune table trouvée!")
                print("   Les migrations n'ont peut-être pas été exécutées.")

            print()

            # Check users table
            if 'users' in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"✅ Table 'users': {count} utilisateur(s)")

            # Check lots table
            if 'lots' in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM lots"))
                count = result.scalar()
                print(f"✅ Table 'lots': {count} lot(s)")

            # Check sales table
            if 'sales' in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM sales"))
                count = result.scalar()
                print(f"✅ Table 'sales': {count} vente(s)")

        await engine.dispose()
        print()
        print("=" * 60)
        print("✅ TOUS LES TESTS DE CONNEXION SONT PASSÉS")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        print()
        print("Vérifications à faire:")
        print("1. Le conteneur PostgreSQL est-il démarré?")
        print("   docker ps | grep postgres")
        print()
        print("2. Le port 5432 est-il accessible?")
        print("   nc -zv localhost 5432")
        print()
        print("3. Les identifiants sont-ils corrects?")
        print(f"   URL: {DATABASE_URL}")
        print()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
