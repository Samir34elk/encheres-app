#!/bin/bash

echo "=========================================="
echo "CONFIGURATION COMPLÈTE DE LA BASE DE DONNÉES"
echo "=========================================="
echo

# Étape 1: Installer l'extension pg_trgm
echo "ÉTAPE 1/3: Installation de l'extension pg_trgm"
echo "----------------------------------------------"
sudo docker exec encheres_db psql -U postgres -d encheres -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de l'installation de pg_trgm"
    exit 1
fi

echo "✅ Extension pg_trgm installée"
echo

# Étape 2: Créer les tables
echo "ÉTAPE 2/3: Création des tables"
echo "----------------------------------------------"
sudo docker exec encheres_backend python3 /app/init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la création des tables"
    exit 1
fi

echo "✅ Tables créées"
echo

# Étape 3: Vérifier les tables
echo "ÉTAPE 3/3: Vérification des tables créées"
echo "----------------------------------------------"
sudo docker exec encheres_db psql -U postgres -d encheres -c "
SELECT
    schemaname,
    tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
"

echo
echo "Comptage des données:"
sudo docker exec encheres_db psql -U postgres -d encheres -c "
SELECT
    'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'lots', COUNT(*) FROM lots
UNION ALL
SELECT 'sales', COUNT(*) FROM sales
UNION ALL
SELECT 'favorites', COUNT(*) FROM favorites
UNION ALL
SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL
SELECT 'notifications', COUNT(*) FROM notifications
UNION ALL
SELECT 'price_history', COUNT(*) FROM price_history
UNION ALL
SELECT 'comments', COUNT(*) FROM comments;
"

echo
echo "=========================================="
echo "✅ CONFIGURATION TERMINÉE AVEC SUCCÈS!"
echo "=========================================="
echo
echo "🎉 Votre base de données est prête!"
echo
echo "Prochaines étapes:"
echo "1. Testez l'API:"
echo "   python3 test_api.py"
echo
echo "2. Ou testez manuellement l'inscription:"
echo "   curl -X POST http://localhost:8000/api/v1/auth/register \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"password123\",\"full_name\":\"Test User\"}'"
echo
echo "3. Accédez au frontend:"
echo "   http://localhost:5173"
echo
