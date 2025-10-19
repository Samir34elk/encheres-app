#!/bin/bash

echo "🚀 Configuration Locale - Enchères du Domaine"
echo "=============================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier Python
echo "🐍 Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    echo "Installez Python 3 avec: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 trouvé: $(python3 --version)${NC}"

# Vérifier Node.js
echo ""
echo "📦 Vérification de Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js n'est pas installé${NC}"
    echo "Installez Node.js avec: sudo apt install nodejs npm"
    exit 1
fi
echo -e "${GREEN}✅ Node.js trouvé: $(node --version)${NC}"
echo -e "${GREEN}✅ npm trouvé: $(npm --version)${NC}"

# Vérifier PostgreSQL
echo ""
echo "🗄️  Vérification de PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL n'est pas installé${NC}"
    echo "Pour installer PostgreSQL:"
    echo "  sudo apt update"
    echo "  sudo apt install postgresql postgresql-contrib"
    echo ""
    echo -e "${YELLOW}Voulez-vous continuer sans PostgreSQL ? (on utilisera SQLite)${NC}"
    read -p "Continuer ? (o/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        exit 1
    fi
    USE_SQLITE=true
else
    echo -e "${GREEN}✅ PostgreSQL trouvé${NC}"
    USE_SQLITE=false
fi

echo ""
echo "📝 Configuration des fichiers d'environnement..."

# Créer .env
if [ ! -f .env ]; then
    cp .env.example .env

    # Générer une clé secrète
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    if [ "$USE_SQLITE" = true ]; then
        # Utiliser SQLite
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:///./encheres.db|g" .env
        sed -i "s|DATABASE_URL_SYNC=.*|DATABASE_URL_SYNC=sqlite:///./encheres.db|g" .env
    else
        # Utiliser PostgreSQL local
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/encheres|g" .env
        sed -i "s|DATABASE_URL_SYNC=.*|DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/encheres|g" .env
    fi

    # Mettre à jour la clé secrète
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env

    # Désactiver Redis (optionnel en local)
    sed -i "s|REDIS_URL=.*|REDIS_URL=redis://localhost:6379/0|g" .env

    echo -e "${GREEN}✅ Fichier .env créé et configuré${NC}"
else
    echo -e "${YELLOW}⚠️  .env existe déjà${NC}"
fi

# Créer frontend/.env
if [ ! -f frontend/.env ]; then
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✅ Fichier frontend/.env créé${NC}"
else
    echo -e "${YELLOW}⚠️  frontend/.env existe déjà${NC}"
fi

echo ""
echo "🔧 Installation des dépendances backend..."
cd backend

# Créer environnement virtuel
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Environnement virtuel créé${NC}"
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
echo "📦 Installation des packages Python..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# Installer Playwright
echo "🎭 Installation de Playwright..."
playwright install chromium

echo -e "${GREEN}✅ Backend configuré${NC}"

cd ..

echo ""
echo "🎨 Installation des dépendances frontend..."
cd frontend

# Installer les dépendances npm
npm install

echo -e "${GREEN}✅ Frontend configuré${NC}"

cd ..

# Créer la base de données si PostgreSQL
if [ "$USE_SQLITE" = false ]; then
    echo ""
    echo "🗄️  Configuration de la base de données PostgreSQL..."

    # Vérifier si la base existe
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw encheres; then
        echo -e "${YELLOW}⚠️  La base 'encheres' existe déjà${NC}"
    else
        echo "Création de la base de données 'encheres'..."
        sudo -u postgres createdb encheres
        echo -e "${GREEN}✅ Base de données créée${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅✅✅ Installation terminée ! ✅✅✅${NC}"
echo ""
echo "📋 Pour lancer l'application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "🌐 URLs d'accès:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Astuce: Utilisez ./run-local.sh pour tout lancer automatiquement"
echo ""
