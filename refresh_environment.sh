#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BOOTSTRAP_MAX_PAGES="${BOOTSTRAP_MAX_PAGES:-1}"
BOOTSTRAP_LIMIT="${BOOTSTRAP_LIMIT:-5}"
BOOTSTRAP_STALENESS="${BOOTSTRAP_STALENESS:-24}"

section() {
  echo
  echo "============================================"
  echo "📦 $1"
  echo "============================================"
  echo
}

fail() {
  echo
  echo "❌ $1"
  exit 1
}

# Vérification des prérequis
section "Vérification des prérequis"
command -v docker >/dev/null 2>&1 || fail "Docker est requis."
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
else
  fail "Aucune commande docker compose disponible."
fi
command -v npm >/dev/null 2>&1 || fail "npm est requis."
command -v python3 >/dev/null 2>&1 || fail "python3 est requis."

# Installation des dépendances backend (env Python local)
section "Installation des dépendances backend"
PY_ENV_DIR="$ROOT_DIR/backend/.venv"
if [ ! -d "$PY_ENV_DIR" ]; then
  python3 -m venv "$PY_ENV_DIR"
fi
source "$PY_ENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
deactivate

# Installation des dépendances frontend
section "Installation des dépendances frontend"
(
  cd frontend
  npm install
)

# Démarrage / build des conteneurs
section "Démarrage de l'infrastructure Docker"
sudo $COMPOSE_CMD up -d --build db redis backend frontend

# Attente de la base de données
section "Attente de la disponibilité PostgreSQL"
MAX_RETRIES=20
RETRY=0
until sudo docker exec encheres_db pg_isready -U postgres >/dev/null 2>&1; do
  ((RETRY++))
  if [ "$RETRY" -ge "$MAX_RETRIES" ]; then
    fail "PostgreSQL ne répond pas après $MAX_RETRIES tentatives."
  fi
  sleep 2
done
echo "✅ PostgreSQL est prêt."

# Migration / création des tables
section "Mise à jour du schéma de base de données"
sudo ./setup_database.sh

# Découverte des ventes et scraping initial
section "Initialisation des ventes et lots"
BOOTSTRAP_ARGS=()
if [ -n "${BOOTSTRAP_MAX_PAGES}" ]; then
  BOOTSTRAP_ARGS+=(--max-pages "$BOOTSTRAP_MAX_PAGES")
fi
if [ -n "${BOOTSTRAP_LIMIT}" ]; then
  BOOTSTRAP_ARGS+=(--limit "$BOOTSTRAP_LIMIT")
fi
if [ -n "${BOOTSTRAP_STALENESS}" ]; then
  BOOTSTRAP_ARGS+=(--staleness-hours "$BOOTSTRAP_STALENESS")
fi
sudo docker exec encheres_backend python -m app.scripts.bootstrap_data "${BOOTSTRAP_ARGS[@]}"

# Tests de fumée API
section "Tests API"
source "$PY_ENV_DIR/bin/activate"
python test_db_connection.py
python test_api.py
deactivate

section "Terminé"
echo "🎉 Environnement prêt. Frontend disponible sur http://localhost:5173"
