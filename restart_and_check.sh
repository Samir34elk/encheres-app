#!/bin/bash

echo "=========================================="
echo "Redémarrage de l'application"
echo "=========================================="
echo

# Fonction pour afficher les logs
show_logs() {
    echo "Affichage des logs backend..."
    if command -v docker &> /dev/null; then
        if docker logs projet_encheres-backend-1 --tail 100 2>/dev/null; then
            return 0
        elif docker compose logs backend --tail 100 2>/dev/null; then
            return 0
        elif docker-compose logs backend --tail 100 2>/dev/null; then
            return 0
        fi
    fi
    echo "❌ Impossible d'accéder aux logs"
    echo "Essayez: sudo docker logs projet_encheres-backend-1 --tail 100"
    return 1
}

# Vérifier si docker est accessible
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé ou pas dans le PATH"
    exit 1
fi

# Essayer de redémarrer
echo "📦 Redémarrage du backend..."
if docker restart projet_encheres-backend-1 2>/dev/null; then
    echo "✅ Backend redémarré"
elif docker compose restart backend 2>/dev/null; then
    echo "✅ Backend redémarré (compose)"
elif docker-compose restart backend 2>/dev/null; then
    echo "✅ Backend redémarré (docker-compose)"
else
    echo "❌ Impossible de redémarrer le backend"
    echo "Essayez: sudo docker restart projet_encheres-backend-1"
    echo "Ou: cd $PWD && sudo docker-compose restart backend"
    exit 1
fi

echo
echo "⏳ Attente du démarrage (5 secondes)..."
sleep 5

echo
echo "=========================================="
echo "Logs du backend:"
echo "=========================================="
show_logs

echo
echo "=========================================="
echo "Test de l'API:"
echo "=========================================="
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "❌ API non accessible"

echo
echo "=========================================="
echo "Pour lancer les tests:"
echo "python3 test_api.py"
echo "=========================================="
