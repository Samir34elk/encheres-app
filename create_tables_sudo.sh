#!/bin/bash

echo "=========================================="
echo "Création des tables de base de données"
echo "=========================================="
echo

# Vérifier que le conteneur backend existe
if ! sudo docker ps -a | grep -q encheres_backend; then
    echo "❌ Le conteneur encheres_backend n'existe pas"
    echo "Démarrez l'application avec: sudo docker-compose up -d"
    exit 1
fi

echo "📦 Exécution du script d'initialisation dans le conteneur..."
echo

# Exécuter le script Python dans le conteneur backend
sudo docker exec encheres_backend python3 -c "
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
    sudo docker exec encheres_backend python3 -c "
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
    echo "✅ INITIALISATION TERMINÉE"
    echo "=========================================="
    echo
    echo "Prochaines étapes:"
    echo "1. Testez l'API: python3 test_api.py"
    echo "2. Ou testez manuellement l'inscription:"
    echo "   curl -X POST http://localhost:8000/api/v1/auth/register \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"password123\",\"full_name\":\"Test User\"}'"
    echo
else
    echo
    echo "❌ Erreur lors de la création des tables"
    echo "Vérifiez les logs: sudo docker logs encheres_backend --tail 50"
    exit 1
fi
