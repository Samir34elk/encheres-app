#!/bin/bash

echo "🔍 DIAGNOSTIC ET RÉPARATION - Projet Enchères"
echo "=============================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier Docker
echo "📦 Vérification de Docker..."
if ! sudo docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker ne répond pas${NC}"
    echo "Démarrage de Docker..."
    sudo systemctl start docker
    sleep 3
fi

# 2. Vérifier les conteneurs
echo ""
echo "🐳 État des conteneurs :"
sudo docker ps -a --filter "name=encheres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 3. Démarrer les conteneurs s'ils ne sont pas lancés
echo ""
echo "🚀 Vérification et démarrage des conteneurs..."
RUNNING=$(sudo docker ps --filter "name=encheres_backend" --format "{{.Names}}" | wc -l)

if [ "$RUNNING" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Les conteneurs ne sont pas lancés${NC}"
    echo "Démarrage avec docker-compose..."
    cd /home/samir/Bureau/Projet_encheres
    sudo docker-compose up -d
    echo "Attente du démarrage (10 secondes)..."
    sleep 10
else
    echo -e "${GREEN}✅ Les conteneurs sont déjà lancés${NC}"
fi

# 4. Vérifier la base de données
echo ""
echo "🗄️  Vérification de la base de données..."
TABLES=$(sudo docker exec encheres_db psql -U postgres -d encheres -t -c "\dt" 2>/dev/null | grep -c "table")

if [ "$TABLES" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Les tables semblent manquantes${NC}"
    echo "Initialisation de la base de données..."
    sudo ./setup_database.sh
else
    echo -e "${GREEN}✅ Base de données OK ($TABLES tables)${NC}"
fi

# 5. Tester le backend
echo ""
echo "🔧 Test du backend..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo -e "${GREEN}✅ Backend répond correctement${NC}"
    echo "Réponse: $HEALTH"
else
    echo -e "${RED}❌ Backend ne répond pas${NC}"
    echo "Logs du backend :"
    sudo docker logs encheres_backend --tail 20
fi

# 6. Tester le frontend
echo ""
echo "🎨 Test du frontend..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend non accessible${NC}"
    echo "Le frontend doit être lancé manuellement :"
    echo "  cd frontend && npm run dev"
fi

# 7. Résumé
echo ""
echo "=============================================="
echo "📊 RÉSUMÉ"
echo "=============================================="
echo ""
echo "🌐 URLs à tester :"
echo "  - Backend API: http://localhost:8000/docs"
echo "  - Frontend:    http://localhost:5173"
echo ""
echo "🛠️  Commandes utiles :"
echo "  - Logs backend:  sudo docker logs encheres_backend -f"
echo "  - Logs DB:       sudo docker logs encheres_db -f"
echo "  - Redémarrer:    sudo docker-compose restart"
echo "  - Arrêter:       sudo docker-compose down"
echo ""
echo "💡 Pour éviter d'utiliser sudo à chaque fois :"
echo "   sudo usermod -aG docker \$USER"
echo "   newgrp docker"
echo ""
