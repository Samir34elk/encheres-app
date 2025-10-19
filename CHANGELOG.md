# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [2.0.0] - 2025-10-20

### 🔒 Sécurité (CRITIQUE)

#### Ajouté
- **Rate Limiting** sur tous les endpoints d'authentification (5 req/min)
- **httpOnly Cookies** pour le stockage des tokens JWT (protection XSS)
- **SECRET_KEY** dynamique générée automatiquement si non fournie
- **CORS restreint** avec whitelist d'origines et méthodes limitées
- **Validation** de la longueur minimum de SECRET_KEY (32 caractères)
- **Headers de sécurité** configurés (SameSite, Secure en production)

#### Modifié
- Migration des tokens de localStorage vers httpOnly cookies
- Refactorisation de l'authentification backend/frontend
- CORS: méthodes limitées à GET, POST, PUT, DELETE, PATCH, OPTIONS
- CORS: headers limités aux essentiels

#### Sécurisé
- Protection contre attaques brute-force via rate limiting
- Protection XSS via httpOnly cookies
- Protection CSRF via SameSite cookies
- Pooling de connexions DB optimisé (20 connexions, overflow 10)

### 🧪 Tests

#### Ajouté
- **Suite complète de tests backend** (pytest)
  - `test_config.py`: Tests de configuration
  - `test_security.py`: Tests de sécurité (rate limiting, XSS, SQL injection)
  - `test_auth.py`: Tests d'authentification
  - `test_lots.py`: Tests des endpoints lots
  - `test_main.py`: Tests des endpoints principaux
  - Fixtures: client, test_db, test_user, admin_user, auth_headers

- **Suite complète de tests frontend** (Vitest)
  - Tests du store d'authentification
  - Tests des composants (Navbar)
  - Tests des pages (LoginPage)
  - Tests des utilitaires (validation)
  - Configuration Vitest + Testing Library

- **Configuration de tests**
  - `pytest.ini`: Configuration pytest avec couverture
  - `vitest.config.ts`: Configuration Vitest
  - `requirements-test.txt`: Dépendances de test Python
  - Scripts npm: `test`, `test:ui`, `test:coverage`

### 🚀 CI/CD

#### Ajouté
- **GitHub Actions Pipeline** complet
  - Workflow `ci.yml`: Tests automatisés backend + frontend
  - Workflow `deploy.yml`: Déploiement automatique sur tags
  - Tests avec PostgreSQL et Redis en services
  - Audit de sécurité (Trivy, Safety, npm audit)
  - Build Docker automatique
  - Upload de couverture vers Codecov
  - Linting et quality checks

- **Dependabot** configuré
  - Mises à jour automatiques Python (pip)
  - Mises à jour automatiques JavaScript (npm)
  - Mises à jour Docker
  - Mises à jour GitHub Actions

### 📚 Documentation

#### Ajouté
- `SECURITY.md`: Guide complet de sécurité
  - Mesures implémentées
  - Configuration production
  - Checklist déploiement
  - Procédure de signalement de vulnérabilités
  - Audit de sécurité

- `TESTING.md`: Guide complet des tests
  - Instructions backend (pytest)
  - Instructions frontend (Vitest)
  - Tests E2E avec Playwright
  - Couverture de code
  - Bonnes pratiques

- `CHANGELOG.md`: Ce fichier
  - Suivi des versions
  - Changements documentés

### 🐛 Corrections

#### Corrigé
- SECRET_KEY par défaut exposée (maintenant générée dynamiquement)
- Tokens stockés en clair dans localStorage (migration vers httpOnly cookies)
- Absence de rate limiting (ajouté sur auth endpoints)
- CORS trop permissif (restreint)
- Pool de connexions DB non optimisé (ajout de pool_size, max_overflow)

### ⚠️ Breaking Changes

- **Authentication**: Les tokens ne sont plus retournés dans localStorage par défaut
  - Migration vers httpOnly cookies
  - Compatibilité backward maintenue temporairement
  - Mise à jour requise pour le frontend

- **API**: Nouvelle logique d'authentification
  - Cookies envoyés automatiquement
  - Header Authorization toujours accepté (fallback)

### 🔧 Améliorations

#### Backend
- Optimisation du pooling de connexions DB
- Validation améliorée de la configuration
- Warnings si DEBUG=True ou SECRET_KEY faible
- Meilleure gestion des erreurs

#### Frontend
- API client configuré avec `withCredentials: true`
- Logout appelle backend pour clear cookies
- CheckAuth ne dépend plus de localStorage

## [1.0.0] - 2025-10-19

### Ajouté
- Application web de suivi des enchères
- Backend FastAPI avec SQLAlchemy
- Frontend React + TypeScript + Tailwind
- Authentification JWT
- Système de favoris
- Scraping automatique avec Playwright
- Mode dark
- Filtres et recherche temps réel
- Docker Compose pour développement

## Prochaines Versions

### [2.1.0] - Planifié
- [ ] Refactorisation LotsPage.tsx (découpage en composants)
- [ ] Amélioration accessibilité (ARIA, contraste WCAG 2.1)
- [ ] Optimisation requêtes DB (cache Redis, résolution N+1)
- [ ] Monitoring centralisé (Prometheus + Grafana)
- [ ] Tests E2E avec Playwright
- [ ] Documentation API (Swagger UI amélioré)

### [3.0.0] - Planifié
- [ ] WebSocket pour notifications temps réel
- [ ] Internationalisation complète (i18n)
- [ ] Export CSV/PDF des lots
- [ ] Statistiques avancées
- [ ] Mode hors-ligne (PWA)
- [ ] Migration vers Kubernetes

---

**Légende**
- 🔒 Sécurité
- 🧪 Tests
- 🚀 CI/CD
- 📚 Documentation
- 🐛 Corrections
- ⚠️ Breaking Changes
- 🔧 Améliorations
