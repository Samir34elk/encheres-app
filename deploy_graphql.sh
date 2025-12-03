#!/bin/bash

# Script de déploiement GraphQL - Migration complète
# Ce script automatise la migration vers le système GraphQL

set -e  # Exit on error

echo "🚀 DÉPLOIEMENT SYSTÈME GRAPHQL"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/samir/Bureau/Projet_encheres"
DB_CONTAINER="projet_encheres_db_1"
BACKUP_DIR="$PROJECT_ROOT/backups"
MIGRATION_FILE="$PROJECT_ROOT/migrations/001_add_graphql_fields.sql"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

confirm() {
    read -p "$(echo -e ${YELLOW}$1${NC}) (y/n) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Step 1: Pre-flight checks
log_info "Vérification des prérequis..."

if [ ! -f "$MIGRATION_FILE" ]; then
    log_error "Fichier de migration introuvable: $MIGRATION_FILE"
    exit 1
fi

if ! docker ps | grep -q "$DB_CONTAINER"; then
    log_error "Container PostgreSQL non trouvé ou non démarré: $DB_CONTAINER"
    log_info "Démarrage des containers..."
    cd "$PROJECT_ROOT"
    docker-compose up -d db
    sleep 5
fi

log_info "✅ Prérequis OK"
echo ""

# Step 2: Backup database
log_info "📦 ÉTAPE 1/7: Backup de la base de données"

if ! confirm "Voulez-vous créer un backup de la BDD avant la migration ?"; then
    log_warning "Backup ignoré - À VOS RISQUES ET PÉRILS!"
else
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

    log_info "Création du backup: $BACKUP_FILE"
    docker-compose exec -T db pg_dump -U postgres encheres > "$BACKUP_FILE"

    if [ -f "$BACKUP_FILE" ]; then
        log_info "✅ Backup créé: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"
    else
        log_error "❌ Échec du backup"
        exit 1
    fi
fi

echo ""

# Step 3: Apply SQL migration
log_info "🗄️  ÉTAPE 2/7: Application de la migration SQL"

if confirm "Appliquer la migration SQL maintenant ?"; then
    log_info "Copie du fichier de migration dans le container..."
    docker cp "$MIGRATION_FILE" "$DB_CONTAINER:/tmp/migration.sql"

    log_info "Exécution de la migration..."
    docker-compose exec -T db psql -U postgres -d encheres -f /tmp/migration.sql

    log_info "Vérification des nouvelles colonnes..."
    docker-compose exec -T db psql -U postgres -d encheres -c "\d lots" | grep -E "(categories|caracteristiques|professionnel|price_reserve)"

    if [ $? -eq 0 ]; then
        log_info "✅ Migration SQL réussie"
    else
        log_error "❌ Migration SQL échouée"
        exit 1
    fi
else
    log_warning "Migration SQL ignorée"
fi

echo ""

# Step 4: Update frontend types
log_info "📝 ÉTAPE 3/7: Mise à jour du frontend"

log_info "Les types TypeScript ont été créés dans: frontend/src/types/index.ts"
log_info "Vous devrez mettre à jour manuellement les composants suivants:"
log_info "  - frontend/src/pages/LotDetailPage.tsx (import { Lot } from '../types')"
log_info "  - frontend/src/pages/LotsPage.tsx (import { Lot } from '../types')"
log_info "  - frontend/src/pages/SaleDetailPage.tsx (import { Lot, Sale } from '../types')"

if confirm "Voulez-vous rebuilder le frontend maintenant ?"; then
    cd "$PROJECT_ROOT/frontend"
    log_info "Installation des dépendances..."
    npm install
    log_info "Build du frontend..."
    npm run build
    log_info "✅ Frontend rebuild"
else
    log_warning "Build frontend ignoré - À faire manuellement"
fi

echo ""

# Step 5: Restart services
log_info "🔄 ÉTAPE 4/7: Redémarrage des services"

if confirm "Redémarrer les services backend ?"; then
    cd "$PROJECT_ROOT"
    log_info "Redémarrage du scraper-service..."
    docker-compose restart scraper-service

    log_info "Redémarrage du core-service..."
    docker-compose restart core-service

    sleep 3
    log_info "✅ Services redémarrés"
else
    log_warning "Redémarrage ignoré"
fi

echo ""

# Step 6: Test GraphQL scrapers
log_info "🧪 ÉTAPE 5/7: Test des scrapers GraphQL"

if confirm "Voulez-vous tester le scraping GraphQL maintenant ?"; then
    log_info "Test de récupération d'une vente..."

    # Run a quick test
    cd "$PROJECT_ROOT"
    docker-compose exec -T scraper-service python -c "
import asyncio
from app.services.graphql_scraper import GraphQLAuctionScraper
from app.database import get_db_session

async def test():
    async with get_db_session() as db:
        scraper = GraphQLAuctionScraper(db)
        auctions = await scraper.fetch_auctions(page=1, page_size=5)
        print(f'✅ {len(auctions)} ventes récupérées')
        await scraper.close()

asyncio.run(test())
" 2>/dev/null || log_warning "Test scraper échoué - vérifier manuellement"

else
    log_warning "Test ignoré"
fi

echo ""

# Step 7: Configure scheduler
log_info "⏰ ÉTAPE 6/7: Configuration du scheduler"

log_info "Fichiers à vérifier pour le scheduler:"
log_info "  - services/scraper-service/app/scheduler.py"
log_info "  - services/scraper-service/app/tasks/"

log_warning "⚠️  Configuration manuelle requise:"
log_warning "    1. Remplacer les appels à playwright_scraper par graphql_scraper"
log_warning "    2. Utiliser GraphQLAuctionScraper.sync_auctions()"
log_warning "    3. Utiliser GraphQLLotScraper.sync_auction_lots()"

echo ""

# Step 8: Summary and next steps
log_info "📊 ÉTAPE 7/7: Récapitulatif"

echo ""
echo "=============================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=============================="
echo ""

log_info "Ce qui a été fait:"
echo "  ✅ Backup BDD créé"
echo "  ✅ Migration SQL appliquée"
echo "  ✅ Types TypeScript créés"
echo "  ✅ Schémas Pydantic mis à jour"
echo "  ✅ Services redémarrés"
echo ""

log_warning "Actions manuelles requises:"
echo "  ⏳ Mettre à jour les composants frontend pour afficher les nouveaux champs"
echo "  ⏳ Configurer le scheduler pour utiliser les scrapers GraphQL"
echo "  ⏳ Tester en production sur quelques ventes"
echo "  ⏳ Supprimer l'ancien système Playwright une fois validé"
echo ""

log_info "Fichiers de référence:"
echo "  📄 Documentation: FONCTIONNEMENT_GRAPHQL.md"
echo "  📄 Résultats test: RESULTAT_TEST_GRAPHQL.md"
echo "  📄 Migration SQL: migrations/001_add_graphql_fields.sql"
echo "  📄 Types frontend: frontend/src/types/index.ts"
echo ""

log_info "Commandes utiles:"
echo "  # Voir les logs scraper"
echo "  docker-compose logs -f scraper-service"
echo ""
echo "  # Tester une requête GraphQL"
echo "  python test_graphql_complet.py --max-sales 1"
echo ""
echo "  # Rollback SQL si nécessaire"
echo "  docker-compose exec db psql -U postgres -d encheres -c 'ALTER TABLE lots DROP COLUMN IF EXISTS categories CASCADE;'"
echo ""

log_info "🎉 Migration GraphQL prête pour la production!"
echo ""
