"""Script pour créer les tables de la base de données"""
import asyncio
from app.db.session import Base, engine

# Import de tous les modèles
from app.models.user import User
from app.models.lot import Lot
from app.models.sale import Sale
from app.models.favorite import Favorite
from app.models.alert import Alert
from app.models.notification import Notification
from app.models.price_history import PriceHistory
from app.models.comment import Comment

async def init_db():
    """Créer toutes les tables"""
    print("Création des tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables créées avec succès!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
