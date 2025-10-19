#!/bin/bash

echo "=========================================="
echo "Installation des extensions PostgreSQL"
echo "=========================================="
echo

# Installer l'extension pg_trgm
echo "📦 Installation de l'extension pg_trgm..."
sudo docker exec encheres_db psql -U postgres -d encheres -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

if [ $? -eq 0 ]; then
    echo "✅ Extension pg_trgm installée"
else
    echo "❌ Erreur lors de l'installation de pg_trgm"
    exit 1
fi

echo

# Vérifier les extensions installées
echo "📋 Extensions installées:"
sudo docker exec encheres_db psql -U postgres -d encheres -c "\dx"

echo
echo "=========================================="
echo "✅ Extensions installées avec succès!"
echo "=========================================="
echo
echo "Maintenant, créez les tables avec:"
echo "  sudo docker exec encheres_backend python3 /app/init_db.py"
