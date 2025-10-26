# Architecture Microservices - Projet Enchères

## Vue d'ensemble

Ce dossier contient la nouvelle architecture microservices qui remplace le backend monolithique et supprime la dépendance à GitHub Actions.

## Structure

```
services/
├── shared/                    # Bibliothèque partagée entre tous les services
│   ├── config/               # Configuration de base
│   ├── models/               # Modèles partagés
│   ├── schemas/              # Schémas Pydantic partagés
│   └── utils/                # Utilitaires (HTTP client, message bus)
│
├── auth-service/             # Service d'authentification (Port 8001)
│   └── app/
│       ├── api/              # Endpoints d'authentification
│       ├── models/           # Modèle User
│       ├── schemas/          # Schémas User, Token
│       ├── core/             # Security, config
│       └── db/               # Session database
│
├── core-service/             # Service métier principal (Port 8002)
│   └── app/
│       ├── api/              # Endpoints: sales, lots, favorites, alerts
│       ├── models/           # Modèles: Sale, Lot, Favorite, Alert, PriceHistory
│       ├── schemas/          # Schémas correspondants
│       └── services/         # Logique métier
│
├── scraper-service/          # Service de scraping (Port 8003)
│   └── app/                  # ⚠️ REMPLACE GITHUB ACTIONS
│       ├── api/              # Endpoints de contrôle du scraper
│       ├── services/         # Scrapers (Playwright, discovery, batch)
│       ├── scheduler/        # APScheduler pour automatisation
│       └── workers/          # Celery workers pour jobs async
│
├── notification-service/     # Service de notifications (Port 8004)
│   └── app/
│       ├── api/              # Endpoints de notifications
│       ├── models/           # Modèle Notification
│       └── services/         # Email, push, webhooks
│
├── admin-service/            # Service d'administration (Port 8005)
│   └── app/
│       ├── api/              # Endpoints admin, ingestion, stats
│       └── services/         # Admin logic
│
└── api-gateway/              # Gateway (Port 8000)
    └── kong/traefik/nginx    # Configuration du gateway
```

## Services

### 1. Auth Service (Port 8001)
**Responsabilités:**
- Inscription / Connexion
- Gestion des tokens JWT
- OAuth2 (Google, GitHub)
- Gestion des utilisateurs

**Endpoints:**
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/logout`

### 2. Core Service (Port 8002)
**Responsabilités:**
- Gestion des ventes (Sales)
- Gestion des lots (Lots)
- Favoris
- Alertes prix
- Historique des prix

**Endpoints:**
- `/sales/*` - CRUD ventes
- `/lots/*` - CRUD lots
- `/favorites/*` - Gestion favoris
- `/alerts/*` - Gestion alertes

### 3. Scraper Service (Port 8003)
**Responsabilités:** 🎯 **REMPLACE GITHUB ACTIONS**
- Découverte automatique des ventes (toutes les 15 min)
- Scraping des lots (toutes les 15 min)
- Mise à jour des prix favoris (toutes les minutes)
- Découverte complète quotidienne (3h du matin)

**Jobs automatiques (APScheduler):**
1. `scrape_sales_job` - Toutes les 15 minutes
2. `discover_sales_job` - Tous les jours à 3h
3. `update_favorite_prices_job` - Toutes les minutes

**Endpoints:**
- `POST /scraper/trigger` - Déclencher manuellement un job
- `GET /scraper/status` - Status des jobs
- `GET /scraper/jobs` - Liste des jobs
- `POST /scraper/jobs/{job_id}/pause` - Mettre en pause
- `POST /scraper/jobs/{job_id}/resume` - Reprendre

**Technologies:**
- Playwright (scraping web)
- Celery (jobs asynchrones)
- APScheduler (planification)
- Redis (queue)

### 4. Notification Service (Port 8004)
**Responsabilités:**
- Envoi d'emails
- Notifications push
- Webhooks

**Endpoints:**
- `GET /notifications` - Liste notifications
- `POST /notifications/send` - Envoyer notification
- `PATCH /notifications/{id}/read` - Marquer comme lue

### 5. Admin Service (Port 8005)
**Responsabilités:**
- Administration
- Ingestion manuelle de données
- Statistiques
- Logs

**Endpoints:**
- `/admin/*` - Endpoints d'administration
- `/ingestion/*` - Ingestion de données
- `/stats/*` - Statistiques

### 6. API Gateway (Port 8000)
**Responsabilités:**
- Routage vers les microservices
- Rate limiting
- Authentification centralisée
- Load balancing

## Communication inter-services

### HTTP Synchrone
Utilise `shared.utils.ServiceClient` pour les requêtes synchrones entre services.

```python
from shared.utils import ServiceClient

client = ServiceClient(settings.CORE_SERVICE_URL)
result = await client.get("/api/v1/lots/123")
```

### Message Bus Asynchrone (RabbitMQ)
Utilise `shared.utils.MessageBus` pour la communication événementielle.

```python
from shared.utils import MessageBus, EventTypes

bus = MessageBus(settings.RABBITMQ_URL)
await bus.connect()

# Publier un événement
await bus.publish(
    EventTypes.LOT_PRICE_UPDATED,
    {"lot_id": 123, "old_price": 1000, "new_price": 1200}
)

# S'abonner à des événements
await bus.subscribe(
    "notification-queue",
    [EventTypes.LOT_PRICE_UPDATED, "lot.*.updated"],
    callback=handle_price_update
)
```

## Variables d'environnement

### Communes à tous les services
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/encheres
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### Scraper Service (remplace CRON_SECRET GitHub)
```env
SCRAPER_INTERVAL_MINUTES=15
ENABLE_SCRAPER=true
AUCTION_BASE_URL=https://encheres-domaine.gouv.fr
```

## Déploiement

### Docker Compose
```bash
docker-compose -f docker-compose.microservices.yml up -d
```

### Services démarrés:
- PostgreSQL (5432)
- Redis (6379)
- RabbitMQ (5672, 15672 pour l'interface web)
- Auth Service (8001)
- Core Service (8002)
- Scraper Service (8003)
- Notification Service (8004)
- Admin Service (8005)
- API Gateway (8000)

## Migration depuis le monolithe

### Changements clés:
1. ✅ **GitHub Actions supprimé** - Remplacé par le Scraper Service interne
2. ✅ Les workflows `scheduled-jobs.yml` sont maintenant des jobs APScheduler
3. ✅ Communication inter-services via HTTP + RabbitMQ
4. ✅ Base de données partagée (peut être séparée par service si nécessaire)

### Avant (Monolithe + GitHub Actions):
```
Backend API (8000) + GitHub Actions (scraping externe)
```

### Après (Microservices):
```
API Gateway (8000) → Auth (8001)
                   → Core (8002)
                   → Scraper (8003) ← INTERNE, pas de GitHub Actions
                   → Notification (8004)
                   → Admin (8005)
```

## Tests

Chaque service a son propre dossier `tests/`:

```bash
# Tester un service spécifique
cd services/auth-service
pytest tests/

# Tester tous les services
./scripts/test-all-services.sh
```

## Monitoring

- **Logs**: Centralisés via Docker logs ou ELK stack
- **Métriques**: Prometheus endpoints sur chaque service
- **Health checks**: `/health` sur chaque service
- **RabbitMQ UI**: http://localhost:15672 (guest/guest)

## Développement

### Ajouter un nouveau service:
1. Créer le dossier `services/mon-service/`
2. Utiliser `shared/` pour config et utils
3. Ajouter au `docker-compose.microservices.yml`
4. Configurer les routes dans l'API Gateway

### Démarrer en mode développement:
```bash
cd services/auth-service
uvicorn app.main:app --reload --port 8001
```

## Sécurité

- JWT tokens pour authentification
- Rate limiting sur API Gateway
- Validation des inputs avec Pydantic
- CORS configuré par service
- Secrets dans variables d'environnement
- Communication inter-services via réseau Docker privé

## TODO

- [ ] Implémenter tous les endpoints de chaque service
- [ ] Configurer l'API Gateway (Kong/Traefik)
- [ ] Tests d'intégration inter-services
- [ ] Migrations de base de données (Alembic)
- [ ] CI/CD pour microservices
- [ ] Documentation OpenAPI pour chaque service
- [ ] Monitoring et alerting (Prometheus + Grafana)
