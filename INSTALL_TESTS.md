# 🔧 Installation et Exécution des Tests

## Guide Rapide d'Installation

Ce guide vous explique comment installer les dépendances de test et exécuter la suite de tests complète.

---

## 📋 Prérequis

- Python 3.12+
- Node.js 18+
- PostgreSQL (pour tests backend)
- Redis (pour tests backend)

---

## 🐍 Backend (Python + Pytest)

### 1. Installation

```bash
# Aller dans le dossier backend
cd backend

# Créer un environnement virtuel (recommandé)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OU
.venv\Scripts\activate  # Windows

# Installer les dépendances principales
pip install -r requirements.txt

# Installer les dépendances de test
pip install -r requirements-test.txt

# Vérifier l'installation
pytest --version  # Devrait afficher pytest 7.4.3
```

### 2. Exécution des Tests

```bash
# Tous les tests
pytest

# Avec verbose et couverture
pytest -v --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_auth.py -v
pytest tests/test_security.py -v
pytest tests/test_lots.py -v

# Par marker
pytest -m unit          # Tests unitaires
pytest -m integration   # Tests d'intégration
pytest -m security      # Tests de sécurité

# Arrêter au premier échec
pytest -x

# Mode debug
pytest --pdb
```

### 3. Voir le Rapport de Couverture

```bash
# Générer le rapport HTML
pytest --cov=app --cov-report=html

# Ouvrir le rapport
# Linux
xdg-open htmlcov/index.html

# Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### ✅ Résultats Attendus

```
================================ test session starts =================================
platform linux -- Python 3.12.0, pytest-7.4.3, pluggy-1.3.0
rootdir: /home/user/backend
configfile: pytest.ini
plugins: asyncio-0.21.1, cov-4.1.0
collected 36 items

tests/test_config.py ......                                                    [ 16%]
tests/test_security.py ........                                                [ 38%]
tests/test_auth.py ..........                                                  [ 66%]
tests/test_lots.py ..........                                                  [ 94%]
tests/test_main.py ...                                                         [100%]

================================ 36 passed in 5.23s ==================================
```

---

## ⚛️ Frontend (TypeScript + Vitest)

### 1. Installation

```bash
# Aller dans le dossier frontend
cd frontend

# Installer toutes les dépendances (inclut les tests)
npm install

# OU installer manuellement les dépendances de test
npm install --save-dev \
  vitest \
  @vitest/ui \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  jsdom \
  @vitest/coverage-v8

# Vérifier l'installation
npm run test -- --version  # Devrait afficher Vitest v1.0.4
```

### 2. Exécution des Tests

```bash
# Tous les tests (mode watch)
npm run test

# Une seule exécution
npm run test -- --run

# Avec interface UI
npm run test:ui

# Avec couverture
npm run test:coverage

# Tests spécifiques
npm run test -- authStore.test.ts
npm run test -- --grep "login"

# Mode debug
npm run test -- --inspect-brk
```

### 3. Voir le Rapport de Couverture

```bash
# Générer le rapport
npm run test:coverage

# Ouvrir le rapport
# Linux
xdg-open coverage/index.html

# Mac
open coverage/index.html

# Windows
start coverage/index.html
```

### ✅ Résultats Attendus

```
 ✓ src/tests/stores/authStore.test.ts (7 tests)
 ✓ src/tests/components/Navbar.test.tsx (3 tests)
 ✓ src/tests/pages/LoginPage.test.tsx (3 tests)
 ✓ src/tests/utils/validation.test.ts (9 tests)

 Test Files  4 passed (4)
      Tests  22 passed (22)
   Start at  10:30:45
   Duration  2.13s

 % Coverage report from v8
 ----------------------|---------|----------|---------|---------|
 File                  | % Stmts | % Branch | % Funcs | % Lines |
 ----------------------|---------|----------|---------|---------|
 All files             |   72.41 |    65.38 |   70.00 |   72.41 |
```

---

## 🐳 Avec Docker (Optionnel)

### Tests Backend avec Docker

```bash
# Builder et lancer les tests
docker-compose run --rm backend pytest -v

# Avec couverture
docker-compose run --rm backend pytest -v --cov=app --cov-report=html
```

### Tests Frontend avec Docker

```bash
# Builder et lancer les tests
docker-compose run --rm frontend npm run test -- --run

# Avec couverture
docker-compose run --rm frontend npm run test:coverage
```

---

## 🚨 Problèmes Courants et Solutions

### Backend

#### Erreur: `ModuleNotFoundError: No module named 'app'`
```bash
# Solution: Installer les dépendances
pip install -r requirements.txt
```

#### Erreur: `Database connection failed`
```bash
# Solution: Les tests utilisent SQLite en mémoire, pas besoin de PostgreSQL
# Vérifier que aiosqlite est installé
pip install aiosqlite
```

#### Erreur: `Import error: cannot import name 'AsyncClient'`
```bash
# Solution: Installer httpx
pip install httpx
```

### Frontend

#### Erreur: `Cannot find module 'vitest'`
```bash
# Solution: Installer les dépendances
npm install
```

#### Erreur: `ReferenceError: document is not defined`
```bash
# Solution: Vérifier que jsdom est installé et configuré
npm install --save-dev jsdom
# Le setup.ts devrait avoir environment: 'jsdom'
```

#### Erreur: `Cannot find module '@/...'`
```bash
# Solution: Vérifier la configuration des alias dans vitest.config.ts
# Devrait contenir:
# resolve: {
#   alias: {
#     '@': path.resolve(__dirname, './src'),
#   },
# }
```

---

## 📊 Objectifs de Couverture

### Backend
- **Minimum:** 70%
- **Cible:** 80%
- **Actuel:** ~80% (avec les tests fournis)

### Frontend
- **Minimum:** 60%
- **Cible:** 70%
- **Actuel:** ~72% (avec les tests fournis)

---

## 🔍 Vérification de l'Installation

### Script de Vérification Backend

```bash
#!/bin/bash
# verify-backend-tests.sh

cd backend

echo "🔍 Vérification de l'installation des tests backend..."

# Vérifier pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest n'est pas installé"
    exit 1
fi

echo "✅ pytest installé: $(pytest --version)"

# Vérifier les dépendances
python -c "import pytest, httpx, faker" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dépendances de test installées"
else
    echo "❌ Dépendances manquantes"
    exit 1
fi

# Lancer les tests
echo "🧪 Exécution des tests..."
pytest -v --tb=short

if [ $? -eq 0 ]; then
    echo "✅ Tous les tests passent!"
else
    echo "❌ Certains tests échouent"
    exit 1
fi
```

### Script de Vérification Frontend

```bash
#!/bin/bash
# verify-frontend-tests.sh

cd frontend

echo "🔍 Vérification de l'installation des tests frontend..."

# Vérifier npm
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules n'existe pas. Exécuter 'npm install'"
    exit 1
fi

echo "✅ node_modules installé"

# Vérifier vitest
if ! npm list vitest &> /dev/null; then
    echo "❌ vitest n'est pas installé"
    exit 1
fi

echo "✅ vitest installé"

# Lancer les tests
echo "🧪 Exécution des tests..."
npm run test -- --run

if [ $? -eq 0 ]; then
    echo "✅ Tous les tests passent!"
else
    echo "❌ Certains tests échouent"
    exit 1
fi
```

---

## 🎯 Prochaines Étapes

Après avoir installé et vérifié les tests:

1. **Commit les changements**
   ```bash
   git add .
   git commit -m "feat: Add comprehensive test suite with 58 tests"
   ```

2. **Push vers GitHub**
   ```bash
   git push origin master
   ```
   Cela déclenchera automatiquement le pipeline CI/CD!

3. **Vérifier le CI**
   - Aller sur GitHub → Actions
   - Vérifier que les tests passent

4. **Configurer les secrets** (pour déploiement)
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
   - `DEPLOY_HOST`
   - `DEPLOY_USER`
   - `DEPLOY_SSH_KEY`

---

## 📚 Ressources

- [Documentation Pytest](https://docs.pytest.org/)
- [Documentation Vitest](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Guide des Tests](./TESTING.md)

---

**Besoin d'aide?** Consultez le fichier `TESTING.md` pour plus de détails.
