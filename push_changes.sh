#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"

git status -sb

read -p "Proceed with git add/commit/push? [y/N] " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

git add .
git commit -m "$COMMIT_MSG"
git push

echo "Changes pushed successfully."
