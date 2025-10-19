#!/bin/bash
# Script pour vérifier les logs backend

echo "=== Vérification des logs backend ==="
echo

# Méthode 1: Essayer avec docker
if docker logs projet_encheres-backend-1 --tail 50 2>/dev/null; then
    exit 0
fi

# Méthode 2: Essayer avec docker compose
if docker compose logs backend --tail 50 2>/dev/null; then
    exit 0
fi

# Méthode 3: Essayer avec docker-compose
if docker-compose logs backend --tail 50 2>/dev/null; then
    exit 0
fi

# Si rien ne fonctionne
echo "❌ Impossible d'accéder aux logs Docker"
echo "Vous devez ajouter votre utilisateur au groupe docker:"
echo "  sudo usermod -aG docker \$USER"
echo "  newgrp docker"
echo
echo "Ou utiliser sudo:"
echo "  sudo docker logs projet_encheres-backend-1 --tail 50"
