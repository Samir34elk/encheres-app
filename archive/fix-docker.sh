#!/bin/bash
echo "🔧 Diagnostic Docker"
echo "====================================="

# Vérifie si Docker est installé
if ! command -v docker &> /dev/null
then
    echo "❌ Docker n'est pas installé."
    echo "💡 Installez Docker via : https://docs.docker.com/engine/install/"
    exit 1
else
    echo "✅ Docker est installé : $(docker --version)"
fi

# Vérifie si le service Docker tourne
if systemctl is-active --quiet docker; then
    echo "✅ Service Docker actif"
else
    echo "⚠️ Service Docker inactif"
    echo "💡 Démarrez Docker : sudo systemctl start docker"
fi

# Vérifie si le groupe docker existe
if getent group docker > /dev/null 2>&1; then
    echo "✅ Groupe 'docker' existe"
else
    echo "⚠️ Groupe 'docker' n'existe pas"
    echo "💡 Créez-le : sudo groupadd docker"
fi

# Vérifie si l'utilisateur actuel fait partie du groupe docker
USER_GROUPS=$(groups $USER)
if echo "$USER_GROUPS" | grep -qw docker; then
    echo "✅ L'utilisateur '$USER' est dans le groupe docker"
else
    echo "⚠️ L'utilisateur '$USER' n'est pas dans le groupe docker"
    echo "💡 Ajoutez-le : sudo usermod -aG docker $USER"
    echo "💡 Puis faites : newgrp docker ou reconnectez-vous"
fi

# Test rapide Docker
echo "🔍 Test de permissions Docker :"
docker info > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker fonctionne correctement pour l'utilisateur '$USER'"
else
    echo "❌ Problème d'accès Docker"
    echo "💡 Vérifiez que le service tourne et que l'utilisateur est dans le groupe docker"
fi

echo "====================================="
echo "✅ Diagnostic terminé"

