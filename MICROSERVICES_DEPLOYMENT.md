# Guide de Déploiement - Architecture Microservices

## 🎯 Objectif

Ce document explique comment déployer la nouvelle architecture microservices qui **remplace complètement GitHub Actions** pour toutes les tâches automatisées.

## ⚠️ Changements Majeurs

### Avant (Architecture Monolithique)
```
┌─────────────────────────────────────────────────┐
│  Backend Monolithique (FastAPI)                 │
│  - API endpoints                                │
│  - Authentification                             │
│  - Gestion des ventes/lots                      │
│  - Scraping (via GitHub Actions externe)        │
└─────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────┐
│  GitHub Actions (scheduled-jobs.yml)            │
│  - Scraping toutes les 15 minutes               │
│  - Découverte quotidienne                       │
│  - Mise à jour des prix chaque minute           │
└─────────────────────────────────────────────────┘
```

### Après (Architecture Microservices)
```
┌──────────────────────────────────────────────────┐
│  API Gateway (NGINX) - Port 8000                 │
│  - Routage                                       │
│  - Rate limiting                                 │
│  - Load balancing                                │
└─────────────┬────────────────────────────────────┘
              │
    ┌─────────┼────────────────────────┐
    │         │                        │
┌───▼────┐ ┌─▼──────┐ ┌──────────▼────────────────┐
│  Auth  │ │  Core  │ │  Scraper Service (8003)   │
│  8001  │ │  8002  │ │  ✅ REMPLACE GitHub Actions│
│        │ │        │ │  - APScheduler interne     │
│        │ │        │ │  - Jobs automatiques       │
└────────┘ └────────┘ └───────────────────────────┘
```

## 📦 Services Déployés

| Service | Port | Description | Remplace |
|---------|------|-------------|----------|
| **API Gateway** | 8000 | Point d'entrée unique | - |
| **Auth Service** | 8001 | Authentification | Backend /auth |
| **Core Service** | 8002 | Ventes, lots, favoris | Backend /sales, /lots |
| **Scraper Service** | 8003 | **Scraping automatisé** | **GitHub Actions** |
| **Notification Service** | 8004 | Notifications | Backend /notifications |
| **Admin Service** | 8005 | Administration | Backend /admin |

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# Installer Docker et Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 2.0
```

### 2. Configuration

Créer un fichier `.env` à la racine :

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/encheres

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Scraper Service (remplace GitHub Actions)
ENABLE_SCHEDULER=true
SCRAPER_INTERVAL_MINUTES=15
ENABLE_PRICE_UPDATES=true

# Email (for notifications)
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_FROM=noreply@encheres.com
```

### 3. Démarrer tous les services

```bash
# Démarrer tous les microservices
docker-compose -f docker-compose.microservices.yml up -d

# Vérifier que tous les services sont lancés
docker-compose -f docker-compose.microservices.yml ps

# Voir les logs en temps réel
docker-compose -f docker-compose.microservices.yml logs -f

# Voir les logs du Scraper Service uniquement
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

### 4. Vérifier le Déploiement

```bash
# API Gateway
curl http://localhost:8000/health
# → {"status": "healthy"}

# Auth Service
curl http://localhost:8001/health
# → {"status": "healthy"}

# Core Service
curl http://localhost:8002/health
# → {"status": "healthy"}

# Scraper Service (remplace GitHub Actions)
curl http://localhost:8003/health
# → {"status": "healthy", "scheduler_running": true}

# Vérifier les jobs du scheduler
curl http://localhost:8003/api/v1/scraper/jobs
# → Liste des jobs automatiques
```

## 📋 Scraper Service - Remplacement de GitHub Actions

### Jobs Automatiques Configurés

Le **Scraper Service** exécute automatiquement les mêmes tâches que GitHub Actions :

#### 1. Scraping des ventes (toutes les 15 minutes)
- **Avant** : GitHub Actions cron `*/15 * * * *` (prepare-sales + scrape-sales)
- **Maintenant** : APScheduler job `scrape_sales_job`
- **Endpoint** : `GET /api/v1/scraper/jobs`

#### 2. Découverte des ventes (tous les jours à 3h)
- **Avant** : GitHub Actions cron `0 3 * * *` (discover-sales)
- **Maintenant** : APScheduler job `discover_sales_job`

#### 3. Mise à jour des prix favoris (toutes les minutes)
- **Avant** : GitHub Actions cron `* * * * *` (update-favorite-prices)
- **Maintenant** : APScheduler job `update_favorite_prices_job`

### Contrôle Manuel des Jobs

```bash
# Lister tous les jobs
curl http://localhost:8003/api/v1/scraper/jobs

# Déclencher manuellement le scraping
curl -X POST http://localhost:8003/api/v1/scraper/trigger/scrape_sales

# Mettre en pause un job
curl -X POST http://localhost:8003/api/v1/scraper/jobs/scrape_sales/pause

# Reprendre un job
curl -X POST http://localhost:8003/api/v1/scraper/jobs/scrape_sales/resume

# Voir le statut du scheduler
curl http://localhost:8003/api/v1/scraper/status
```

### Logs du Scraper

```bash
# Voir les logs en temps réel
docker-compose -f docker-compose.microservices.yml logs -f scraper-service

# Logs attendus au démarrage :
# ============================================================
# 🚀 Starting Internal Scheduler
#    REPLACES: GitHub Actions (.github/workflows/scheduled-jobs.yml)
# ============================================================
# ✓ Job 1: Scrape sales every 15 minutes
#          (Replaces: GitHub Actions cron '*/15 * * * *')
# ✓ Job 2: Discover sales daily at 3:00 AM
#          (Replaces: GitHub Actions cron '0 3 * * *')
# ✓ Job 3: Update favorite prices every minute
#          (Replaces: GitHub Actions cron '* * * * *')
# ============================================================
# ✅ Scheduler started successfully!
#    GitHub Actions workflows are now REPLACED by internal scheduler
# ============================================================
```

## 🗄️ Base de Données

### Migration depuis le Monolithe

La base de données PostgreSQL est **partagée** entre tous les services. Les migrations Alembic existantes fonctionnent toujours.

```bash
# Appliquer les migrations (depuis n'importe quel service)
docker-compose -f docker-compose.microservices.yml exec core-service alembic upgrade head

# Créer une nouvelle migration
docker-compose -f docker-compose.microservices.yml exec core-service alembic revision --autogenerate -m "Description"
```

## 📊 Monitoring

### RabbitMQ Management UI

Interface web pour surveiller les messages inter-services :

- **URL** : http://localhost:15672
- **User** : guest
- **Password** : guest

### Health Checks

Tous les services exposent un endpoint `/health` :

```bash
#!/bin/bash
# Script pour vérifier tous les services

services=(
    "api-gateway:8000"
    "auth-service:8001"
    "core-service:8002"
    "scraper-service:8003"
    "notification-service:8004"
    "admin-service:8005"
)

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"
    status=$(curl -s http://localhost:$port/health)
    echo "[$name] $status"
done
```

## 🔐 Sécurité

### Variables d'Environnement Sensibles

**⚠️ NE JAMAIS committer ces valeurs dans Git !**

```env
# .env (à créer localement)
SECRET_KEY=votre-clé-secrète-longue-et-complexe
MAIL_PASSWORD=votre-mot-de-passe-email
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```

### Recommandations de Production

1. **SECRET_KEY** : Générer une clé aléatoire de 64+ caractères
2. **Cookies** : Activer `COOKIE_SECURE=true` en HTTPS
3. **CORS** : Limiter `BACKEND_CORS_ORIGINS` aux domaines autorisés
4. **Rate Limiting** : Configurer dans NGINX (déjà fait)
5. **HTTPS** : Utiliser un reverse proxy (Nginx/Traefik) avec certificat SSL

## 🛠️ Maintenance

### Arrêter les Services

```bash
# Arrêter tous les services
docker-compose -f docker-compose.microservices.yml down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose -f docker-compose.microservices.yml down -v
```

### Redémarrer un Service Spécifique

```bash
# Redémarrer uniquement le Scraper Service
docker-compose -f docker-compose.microservices.yml restart scraper-service

# Voir les logs après redémarrage
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

### Mise à Jour d'un Service

```bash
# Rebuild et redémarrer un service
docker-compose -f docker-compose.microservices.yml up -d --build scraper-service
```

## 🧪 Tests

### Tests d'Intégration

```bash
# Tester la communication Auth → Core
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"

# Récupérer le token et tester l'accès aux lots
TOKEN="<votre-token>"
curl http://localhost:8000/api/v1/lots \
  -H "Authorization: Bearer $TOKEN"
```

### Tests du Scraper

```bash
# Tester le déclenchement manuel d'un job
curl -X POST http://localhost:8000/api/v1/scraper/trigger/discover_sales

# Vérifier l'exécution dans les logs
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

## 📈 Performance

### Recommandations

- **CPU** : Minimum 2 cores (4 cores recommandés)
- **RAM** : Minimum 4GB (8GB recommandés)
- **Disk** : SSD recommandé pour PostgreSQL

### Scaling Horizontal

Pour gérer plus de charge, déployer plusieurs instances :

```yaml
# docker-compose.microservices.yml
core-service:
  deploy:
    replicas: 3
```

## 🆘 Troubleshooting

### Le Scraper Service ne démarre pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.microservices.yml logs scraper-service

# Problème : Playwright non installé
# Solution : Rebuild l'image
docker-compose -f docker-compose.microservices.yml up -d --build scraper-service
```

### Les jobs ne s'exécutent pas

```bash
# Vérifier que le scheduler est activé
curl http://localhost:8003/health
# → {"status": "healthy", "scheduler_running": true}

# Si scheduler_running: false, vérifier la config
docker-compose -f docker-compose.microservices.yml exec scraper-service env | grep ENABLE_SCHEDULER
# → ENABLE_SCHEDULER=true
```

### Erreurs de connexion inter-services

```bash
# Vérifier que tous les services sont sur le même réseau
docker network inspect encheres-network

# Tester la connectivité réseau
docker-compose -f docker-compose.microservices.yml exec core-service ping auth-service
```

## 📚 Ressources

- **Architecture** : `services/README.md`
- **Code Source** : `services/<service-name>/`
- **Configuration** : `docker-compose.microservices.yml`
- **Gateway** : `services/api-gateway/nginx.conf`

## ✅ Checklist Post-Déploiement

- [ ] Tous les services démarrent sans erreur
- [ ] `/health` renvoie "healthy" pour chaque service
- [ ] API Gateway route correctement vers les services
- [ ] Scraper Service scheduler est actif
- [ ] Jobs automatiques s'exécutent (vérifier logs après 15 min)
- [ ] RabbitMQ UI accessible (http://localhost:15672)
- [ ] Frontend peut communiquer avec l'API Gateway
- [ ] Migrations de base de données appliquées
- [ ] Variables d'environnement sensibles configurées

## 🎉 Félicitations !

Vous avez migré avec succès vers une architecture microservices !

**GitHub Actions n'est plus nécessaire pour les tâches automatisées** - tout est maintenant géré en interne par le Scraper Service.
