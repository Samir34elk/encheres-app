# 🧪 Guide de Tests

## Vue d'Ensemble

Ce projet dispose d'une suite complète de tests couvrant le backend et le frontend.

## Tests Backend (Python + Pytest)

### Installation

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Exécution

```bash
# Tous les tests
pytest

# Tests avec verbose
pytest -v

# Tests avec couverture
pytest --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_auth.py -v
pytest tests/test_security.py -v

# Tests par marker
pytest -m unit          # Tests unitaires uniquement
pytest -m integration   # Tests d'intégration
pytest -m security      # Tests de sécurité
```

### Structure des Tests

```
backend/tests/
├── conftest.py              # Fixtures et configuration
├── test_config.py           # Tests de configuration
├── test_security.py         # Tests de sécurité
├── test_auth.py             # Tests d'authentification
├── test_lots.py             # Tests endpoints lots
└── test_main.py             # Tests endpoints principaux
```

### Fixtures Disponibles

- `client`: Client HTTP de test
- `test_db`: Session de base de données de test
- `test_user`: Utilisateur de test
- `admin_user`: Utilisateur admin de test
- `auth_headers`: Headers d'authentification
- `admin_headers`: Headers d'authentification admin

### Exemple de Test

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_login(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Tests Frontend (TypeScript + Vitest)

### Installation

```bash
cd frontend
npm install
```

### Exécution

```bash
# Tous les tests
npm run test

# Mode watch
npm run test -- --watch

# UI interactive
npm run test:ui

# Couverture
npm run test:coverage

# Tests spécifiques
npm run test -- authStore.test.ts
```

### Structure des Tests

```
frontend/src/tests/
├── setup.ts                      # Configuration globale
├── stores/
│   └── authStore.test.ts        # Tests du store d'auth
├── components/
│   └── Navbar.test.tsx          # Tests composants
├── pages/
│   └── LoginPage.test.tsx       # Tests pages
└── utils/
    └── validation.test.ts       # Tests utilitaires
```

### Exemple de Test

```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginPage from '@/pages/LoginPage'

describe('LoginPage', () => {
  it('should handle form submission', async () => {
    render(<LoginPage />)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /login/i }))

    expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123')
  })
})
```

## Couverture de Code

### Objectifs

- **Backend**: Minimum 80% de couverture
- **Frontend**: Minimum 70% de couverture

### Voir les Rapports

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm run test:coverage
open coverage/index.html
```

## Tests de Sécurité

### Rate Limiting

```python
@pytest.mark.security
async def test_rate_limiting_auth_endpoint(client: AsyncClient):
    responses = []
    for _ in range(10):
        response = await client.post("/api/v1/auth/login", ...)
        responses.append(response.status_code)

    assert 429 in responses  # Too Many Requests
```

### SQL Injection

```python
@pytest.mark.security
async def test_sql_injection_protection(client: AsyncClient):
    response = await client.get(
        "/api/v1/lots",
        params={"search": "'; DROP TABLE lots; --"}
    )
    assert response.status_code in [200, 400, 422]  # Not 500
```

## Tests E2E (End-to-End)

### Avec Playwright (Recommandé)

```bash
# Installation
npm install -D @playwright/test

# Exécution
npx playwright test

# Mode UI
npx playwright test --ui

# Générer les tests
npx playwright codegen http://localhost:5173
```

### Exemple E2E

```typescript
import { test, expect } from '@playwright/test'

test('user can login and view lots', async ({ page }) => {
  await page.goto('http://localhost:5173')

  // Login
  await page.click('text=Login')
  await page.fill('[name=email]', 'test@example.com')
  await page.fill('[name=password]', 'password123')
  await page.click('button:has-text("Submit")')

  // Verify redirect
  await expect(page).toHaveURL(/.*lots/)

  // Check lots are displayed
  await expect(page.locator('.lot-item')).toHaveCount.greaterThan(0)
})
```

## CI/CD

Les tests s'exécutent automatiquement sur chaque push/PR via GitHub Actions :

- Tests backend avec PostgreSQL
- Tests frontend
- Audit de sécurité
- Rapport de couverture sur Codecov

## Debugging

### Backend

```bash
# Mode debug avec pdb
pytest --pdb tests/test_auth.py

# Logs détaillés
pytest -v --log-cli-level=DEBUG

# Arrêter au premier échec
pytest -x
```

### Frontend

```bash
# Debug dans le navigateur
npm run test:ui

# Logs détaillés
npm run test -- --reporter=verbose

# Un seul fichier
npm run test -- authStore.test.ts
```

## Bonnes Pratiques

1. **Écrire les tests AVANT le code** (TDD)
2. **Un test = une assertion** (principe KISS)
3. **Noms de tests explicites** : `test_user_cannot_access_admin_endpoint`
4. **Isoler les tests** : pas de dépendances entre tests
5. **Mock les services externes** : API, base de données
6. **Tester les cas d'erreur** : pas seulement le happy path

## Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Playwright](https://playwright.dev/)
