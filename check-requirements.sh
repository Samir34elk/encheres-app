#!/bin/bash

echo "🔍 Vérification des prérequis"
echo "=============================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MISSING=0
WARNINGS=0

# Vérifier Python
echo -n "Python 3........."
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${RED}❌ Non installé${NC}"
    echo "   Installez avec: sudo apt install python3 python3-pip python3-venv"
    MISSING=$((MISSING + 1))
fi

# Vérifier pip
echo -n "pip.............."
if command -v pip3 &> /dev/null; then
    VERSION=$(pip3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${RED}❌ Non installé${NC}"
    echo "   Installez avec: sudo apt install python3-pip"
    MISSING=$((MISSING + 1))
fi

# Vérifier Node.js
echo -n "Node.js.........."
if command -v node &> /dev/null; then
    VERSION=$(node --version 2>&1)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${RED}❌ Non installé${NC}"
    echo "   Installez avec: sudo apt install nodejs npm"
    MISSING=$((MISSING + 1))
fi

# Vérifier npm
echo -n "npm.............."
if command -v npm &> /dev/null; then
    VERSION=$(npm --version 2>&1)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${RED}❌ Non installé${NC}"
    echo "   Installez avec: sudo apt install npm"
    MISSING=$((MISSING + 1))
fi

# Vérifier PostgreSQL (optionnel)
echo -n "PostgreSQL......."
if command -v psql &> /dev/null; then
    VERSION=$(psql --version 2>&1 | cut -d' ' -f3)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${YELLOW}⚠️  Non installé${NC} (optionnel - SQLite sera utilisé)"
    echo "   Pour installer: sudo apt install postgresql postgresql-contrib"
    WARNINGS=$((WARNINGS + 1))
fi

# Vérifier Docker (optionnel)
echo -n "Docker..........."
if command -v docker &> /dev/null; then
    VERSION=$(docker --version 2>&1 | cut -d' ' -f3 | cut -d',' -f1)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"

    # Vérifier les permissions
    if docker ps &> /dev/null; then
        echo -e "                 ${GREEN}✅ Permissions OK${NC}"
    else
        echo -e "                 ${YELLOW}⚠️  Permissions manquantes${NC}"
        echo "   Corrigez avec: ./fix-docker.sh"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Non installé${NC} (optionnel - utilisez l'installation locale)"
    echo "   Pour installer: sudo apt install docker.io docker-compose"
    WARNINGS=$((WARNINGS + 1))
fi

# Vérifier Docker Compose (optionnel)
echo -n "Docker Compose..."
if command -v docker-compose &> /dev/null; then
    VERSION=$(docker-compose --version 2>&1 | cut -d' ' -f4 | cut -d',' -f1)
    echo -e "${GREEN}✅ Installé${NC} (version $VERSION)"
else
    echo -e "${YELLOW}⚠️  Non installé${NC} (optionnel - utilisez l'installation locale)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "=============================="

# Résumé
if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les outils essentiels sont installés !${NC}"
    echo ""
    echo "🚀 Vous pouvez lancer l'application avec :"
    echo ""
    echo -e "${BLUE}Option 1 - Installation locale (recommandé) :${NC}"
    echo "  ./setup-local.sh"
    echo "  ./run-local.sh"
    echo ""
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${BLUE}Option 2 - Docker :${NC}"
        echo "  ./start.sh"
    elif docker ps &> /dev/null 2>&1; then
        echo -e "${BLUE}Option 2 - Docker :${NC}"
        echo "  ./start.sh"
    else
        echo -e "${YELLOW}Option 2 - Docker (nécessite correction) :${NC}"
        echo "  ./fix-docker.sh"
        echo "  ./start.sh"
    fi
else
    echo -e "${RED}❌ Il manque $MISSING outil(s) essentiel(s)${NC}"
    echo ""
    echo "Installez les outils manquants et relancez ce script."
    echo ""
    echo "Pour tout installer d'un coup sur Ubuntu/Debian :"
    echo "  sudo apt update"
    echo "  sudo apt install python3 python3-pip python3-venv nodejs npm"
fi

if [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  $WARNINGS avertissement(s)${NC}"
    echo "Ces outils sont optionnels. L'application peut fonctionner sans eux."
fi

echo ""
echo "📚 Documentation :"
echo "  - Voir toutes les options : COMMENT_LANCER.md"
echo "  - Démarrage rapide : DEMARRAGE_RAPIDE.md"
echo "  - Documentation complète : README.md"
echo ""
