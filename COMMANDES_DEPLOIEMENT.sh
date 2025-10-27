#!/bin/bash
# Script de déploiement des microservices
# Généré par Claude Code - 2025-10-27
# À exécuter depuis la racine du projet

set -e

echo "🚀 Déploiement des Microservices Node.js"
echo "========================================"
echo ""

# Vérification qu'on est dans le bon répertoire
if [ ! -f "render.yaml" ]; then
    echo "❌ Erreur: render.yaml non trouvé"
    echo "   Assurez-vous d'être dans /home/samir/Bureau/Projet_encheres"
    exit 1
fi

echo "📁 Répertoire actuel: $(pwd)"
echo ""

# Afficher les fichiers modifiés
echo "📝 Fichiers qui seront commités:"
echo "---"
git status --short
echo ""

# Demander confirmation
read -p "🔍 Voulez-vous continuer avec le commit et push? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Annulé par l'utilisateur"
    exit 1
fi

echo ""
echo "✅ Ajout des fichiers au staging..."
git add .

echo "✅ Création du commit..."
git commit -m "fix: Préparer microservices pour déploiement Render

Corrections majeures:
- Fix Prisma generate (déplacé au runtime dans CMD)
- Généré package-lock.json pour api-gateway
- Fix scraper-service TypeScript errors (DOM lib, strict:false)
- Supprimé import Prisma inutile dans scraper
- Nettoyé configuration Render (un seul render.yaml)
- Tous les builds TypeScript testés et réussis

Services prêts:
✅ auth-service (port 3001)
✅ lots-service (port 3002)
✅ sales-service (port 3003)
✅ scraper-service (port 3004)
✅ notifications-service (port 3005)
✅ api-gateway (port 10000)

Utilise bases existantes:
- PostgreSQL: encheres-db (dpg-d3qns7vdiees73agmvcg-a)
- Redis: encheres-redis (red-d3vck87diees73esn4a0)

Fichiers créés:
- ANALYSE_MICROSERVICES.md (analyse complète)
- DEPLOIEMENT_READY.md (guide de déploiement)
- RESUME_CORRECTIONS.md (résumé)
- microservices/test-docker-builds.sh (tests Docker)
- COMMANDES_DEPLOIEMENT.sh (ce script)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo ""
echo "✅ Commit créé avec succès!"
echo ""

# Demander confirmation pour le push
read -p "🌍 Push vers origin/master maintenant? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  Commit créé mais pas pushé"
    echo "   Pour pusher plus tard: git push origin master"
    exit 0
fi

echo ""
echo "⬆️  Push vers origin/master..."
git push origin master

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT LANCÉ!"
echo "=========================================="
echo ""
echo "📊 Prochaines étapes:"
echo ""
echo "1. 🖥️  Ouvrir Render Dashboard:"
echo "   https://dashboard.render.com"
echo ""
echo "2. 👀 Surveiller les builds des services -v2:"
echo "   - encheres-auth-service-v2"
echo "   - encheres-lots-service-v2"
echo "   - encheres-sales-service-v2"
echo "   - encheres-scraper-service-v2"
echo "   - encheres-notifications-service-v2"
echo "   - encheres-api-gateway-v2"
echo ""
echo "3. ⚙️  Configurer les variables manuelles (après builds):"
echo "   - JWT_SECRET: Copier de auth-service vers autres"
echo "   - SMTP_USER, SMTP_PASS: Pour notifications"
echo ""
echo "4. 🏥 Tester les health checks:"
echo "   curl https://encheres-auth-service-v2.onrender.com/health"
echo "   (Répéter pour chaque service)"
echo ""
echo "5. 📖 Consulter DEPLOIEMENT_READY.md pour plus de détails"
echo ""
echo "🎉 Bonne chance!"
