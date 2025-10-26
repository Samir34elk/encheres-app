#!/bin/bash

# Script de démarrage des microservices
# Remplace GitHub Actions par un scheduler interne

set -e

echo "============================================================"
echo "  🚀 Démarrage de l'Architecture Microservices"
echo "  ✨ GitHub Actions workflows remplacés par le Scraper Service"
echo "============================================================"
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

echo "✓ Docker et Docker Compose détectés"
echo ""

# Vérifier le fichier .env
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé, création..."
    cat > .env <<EOF
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/encheres

# Security
SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')

# Scraper Service (remplace GitHub Actions)
ENABLE_SCHEDULER=true
SCRAPER_INTERVAL_MINUTES=15
ENABLE_PRICE_UPDATES=true

# Email
MAIL_USERNAME=noreply@encheres.com
MAIL_PASSWORD=change-me
MAIL_FROM=noreply@encheres.com
EOF
    echo "✓ Fichier .env créé (pensez à modifier les valeurs)"
    echo ""
fi

# Arrêter les anciens conteneurs
echo "📦 Arrêt des anciens conteneurs..."
docker-compose -f docker-compose.microservices.yml down 2>/dev/null || true
echo ""

# Construire les images
echo "🔨 Construction des images Docker..."
docker-compose -f docker-compose.microservices.yml build
echo ""

# Démarrer les services
echo "🚀 Démarrage des microservices..."
docker-compose -f docker-compose.microservices.yml up -d
echo ""

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10
echo ""

# Vérifier le statut
echo "============================================================"
echo "  📊 Statut des Services"
echo "============================================================"

check_service() {
    local name=$1
    local port=$2
    local url="http://localhost:$port/health"

    if curl -s "$url" &>/dev/null; then
        echo "✅ $name (port $port) - Running"
    else
        echo "❌ $name (port $port) - Failed"
    fi
}

check_service "API Gateway      " 8000
check_service "Auth Service     " 8001
check_service "Core Service     " 8002
check_service "Scraper Service  " 8003
check_service "Notification Svc " 8004
check_service "Admin Service    " 8005

echo ""
echo "============================================================"
echo "  🎯 Services Déployés"
echo "============================================================"
echo ""
echo "  API Gateway:          http://localhost:8000"
echo "  Auth Service:         http://localhost:8001"
echo "  Core Service:         http://localhost:8002"
echo "  Scraper Service:      http://localhost:8003"
echo "  Notification Service: http://localhost:8004"
echo "  Admin Service:        http://localhost:8005"
echo "  RabbitMQ UI:          http://localhost:15672 (guest/guest)"
echo "  Frontend:             http://localhost:5173"
echo ""
echo "============================================================"
echo "  ⚡ Scraper Service - GitHub Actions Remplacé"
echo "============================================================"
echo ""
echo "  Le Scraper Service remplace les workflows GitHub Actions:"
echo "    • Scraping des ventes: toutes les 15 minutes"
echo "    • Découverte des ventes: tous les jours à 3h"
echo "    • Mise à jour des prix: toutes les minutes"
echo ""
echo "  Endpoints de contrôle:"
echo "    • Status: curl http://localhost:8003/health"
echo "    • Jobs:   curl http://localhost:8003/api/v1/scraper/jobs"
echo "    • Logs:   docker-compose -f docker-compose.microservices.yml logs -f scraper-service"
echo ""
echo "============================================================"
echo "  📚 Commandes Utiles"
echo "============================================================"
echo ""
echo "  Voir les logs:      docker-compose -f docker-compose.microservices.yml logs -f"
echo "  Arrêter:            docker-compose -f docker-compose.microservices.yml down"
echo "  Redémarrer:         docker-compose -f docker-compose.microservices.yml restart"
echo "  Status:             docker-compose -f docker-compose.microservices.yml ps"
echo ""
echo "✅ Microservices démarrés avec succès!"
echo ""
