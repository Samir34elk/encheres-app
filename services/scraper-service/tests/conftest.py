import os
import sys

HERE = os.path.dirname(__file__)
# scraper-service/ (pour `app`) et services/ (pour `shared`)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))

# Le moteur SQLAlchemy est créé à l'import (sans connexion) : une URL factice suffit.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
