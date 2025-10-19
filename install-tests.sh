#!/bin/bash

# Script d'installation des dépendances de test
# Version 2.0.0

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Installation des Tests v2.0  ${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Erreur: Ce script doit être exécuté depuis la racine du projet${NC}"
    exit 1
fi

# Backend Tests Installation
echo -e "${YELLOW}📦 Installation des dépendances de test backend...${NC}"
cd backend

if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Création de l'environnement virtuel Python...${NC}"
    python3 -m venv .venv
fi

echo -e "${BLUE}Activation de l'environnement virtuel...${NC}"
source .venv/bin/activate

echo -e "${BLUE}Installation des dépendances principales...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${BLUE}Installation des dépendances de test...${NC}"
pip install -r requirements-test.txt

echo -e "${GREEN}✅ Dépendances backend installées${NC}"

# Verify installation
echo -e "${BLUE}Vérification de l'installation...${NC}"
pytest --version

cd ..

# Frontend Tests Installation
echo ""
echo -e "${YELLOW}📦 Installation des dépendances de test frontend...${NC}"
cd frontend

echo -e "${BLUE}Installation via npm...${NC}"
npm install

echo -e "${GREEN}✅ Dépendances frontend installées${NC}"

# Verify installation
echo -e "${BLUE}Vérification de l'installation...${NC}"
npm run test -- --version || echo "Vitest installé"

cd ..

# Run tests to verify
echo ""
echo -e "${YELLOW}🧪 Exécution des tests pour vérification...${NC}"
echo ""

# Backend tests
echo -e "${BLUE}Tests Backend:${NC}"
cd backend
source .venv/bin/activate
pytest -v --tb=short || {
    echo -e "${YELLOW}⚠️  Certains tests backend ont échoué. Vérifiez la configuration.${NC}"
}
cd ..

# Frontend tests
echo ""
echo -e "${BLUE}Tests Frontend:${NC}"
cd frontend
npm run test -- --run || {
    echo -e "${YELLOW}⚠️  Certains tests frontend ont échoué. Vérifiez la configuration.${NC}"
}
cd ..

# Success message
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Installation terminée!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Prochaines étapes:${NC}"
echo ""
echo -e "  1. Lancer les tests backend:"
echo -e "     ${YELLOW}cd backend && source .venv/bin/activate && pytest -v${NC}"
echo ""
echo -e "  2. Lancer les tests frontend:"
echo -e "     ${YELLOW}cd frontend && npm run test${NC}"
echo ""
echo -e "  3. Voir la couverture backend:"
echo -e "     ${YELLOW}cd backend && pytest --cov=app --cov-report=html${NC}"
echo ""
echo -e "  4. Voir la couverture frontend:"
echo -e "     ${YELLOW}cd frontend && npm run test:coverage${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "  - Guide d'installation: ${YELLOW}INSTALL_TESTS.md${NC}"
echo -e "  - Guide des tests: ${YELLOW}TESTING.md${NC}"
echo -e "  - Guide de sécurité: ${YELLOW}SECURITY.md${NC}"
echo -e "  - Résumé des améliorations: ${YELLOW}IMPROVEMENTS_SUMMARY.md${NC}"
echo ""
