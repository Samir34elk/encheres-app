#!/bin/bash

echo "=========================================="
echo "Création des tables de base de données"
echo "=========================================="
echo

# Vérifier que le conteneur backend existe
if ! docker ps -a | grep -q encheres_backend; then
    echo "❌ Le conteneur encheres_backend n'existe pas"
    echo "Démarrez l'application avec: docker-compose up -d"
    exit 1
fi

# Exécuter le script Python dans le conteneur backend
echo "📦 Exécution du script d'initialisation dans le conteneur..."
echo

docker exec encheres_backend python3 -c "
import asyncio
from app.db.session import Base, engine

# Import tous les modèles
from app.models.user import User
from app.models.lot import Lot
from app.models.sale import Sale
from app.models.favorite import Favorite
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.price_history import PriceHistory
from app.models.comment import Comment

async def create_tables():
    print('🔧 Création des tables...')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tables créées avec succès!')
    await engine.dispose()

asyncio.run(create_tables())
"

if [ $? -eq 0 ]; then
    echo
    echo "=========================================="
    echo "✅ Tables créées avec succès!"
    echo "=========================================="
    echo
    echo "Vérification des tables..."
    docker exec encheres_backend python3 -c "
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            \"\"\"SELECT table_name FROM information_schema.tables
               WHERE table_schema = 'public' ORDER BY table_name\"\"\"
        ))
        tables = [row[0] for row in result]
        print('\\n📊 Tables disponibles:')
        for table in tables:
            print(f'   ✓ {table}')

        # Compter les utilisateurs
        result = await conn.execute(text('SELECT COUNT(*) FROM users'))
        count = result.scalar()
        print(f'\\n👥 Utilisateurs: {count}')

        # Compter les lots
        result = await conn.execute(text('SELECT COUNT(*) FROM lots'))
        count = result.scalar()
        print(f'📦 Lots: {count}')

        # Compter les ventes
        result = await conn.execute(text('SELECT COUNT(*) FROM sales'))
        count = result.scalar()
        print(f'🏪 Ventes: {count}')

    await engine.dispose()

asyncio.run(check_tables())
"

    echo
    echo "=========================================="
    echo "Prochaines étapes:"
    echo "1. Testez l'API: python3 test_api.py"
    echo "2. Créez un utilisateur admin (voir GUIDE_RESOLUTION.md)"
    echo "3. Lancez le scraping"
    echo "=========================================="
else
    echo
    echo "❌ Erreur lors de la création des tables"
    echo "Vérifiez les logs: docker logs encheres_backend"
fi
