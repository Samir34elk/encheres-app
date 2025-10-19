#!/bin/bash
set -euo pipefail

REMOTE_URL="${1:-}"

if ! command -v git >/dev/null 2>&1; then
  echo "❌ git n'est pas installé."
  exit 1
fi

if [ -d .git ]; then
  echo "ℹ️ Dépôt Git déjà initialisé."
else
  echo "📦 Initialisation du dépôt Git…"
  git init
fi

echo "📄 Ajout des fichiers au commit initial…"
git add .

DEFAULT_MESSAGE="Initial commit"
read -rp "Message de commit [${DEFAULT_MESSAGE}] : " COMMIT_MSG
COMMIT_MSG=${COMMIT_MSG:-$DEFAULT_MESSAGE}

if git diff --cached --quiet; then
  echo "⚠️ Aucun fichier à committer."
else
  git commit -m "$COMMIT_MSG"
fi

if [ -n "$REMOTE_URL" ]; then
  if git remote | grep -q "^origin$"; then
    echo "ℹ️ Remote 'origin' déjà configuré."
  else
    echo "🔗 Ajout du remote origin : $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
  fi

  read -rp "Souhaitez-vous pousser vers 'origin'? (o/N) " PUSH_REPLY
  case "${PUSH_REPLY,,}" in
    o|oui|y|yes)
      CURRENT_BRANCH=$(git branch --show-current)
      if [ -z "$CURRENT_BRANCH" ]; then
        read -rp "Nom de la branche à créer (ex: main) : " NEW_BRANCH
        CURRENT_BRANCH=${NEW_BRANCH:-main}
        git branch -M "$CURRENT_BRANCH"
      fi
      git push -u origin "$CURRENT_BRANCH"
      ;;
    *)
      echo "ℹ️ Poussée vers le remote annulée."
      ;;
  esac
else
  echo "ℹ️ Aucun remote fourni. Vous pouvez l’ajouter plus tard avec:"
  echo "   git remote add origin <URL>"
fi
