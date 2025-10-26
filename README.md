# Enchères du Domaine - Architecture Microservices

## 🎯 Vue d'Ensemble

Plateforme de suivi des enchères publiques du domaine, construite avec une **architecture microservices moderne**.

**Point clé:** Toute l'automatisation (scraping, découverte, mise à jour des prix) est **gérée en interne** par le Scraper Service. Plus besoin de GitHub Actions !

---

## 🏗️ Architecture

```
┌────────────────────────────────────────┐
│    API Gateway / Frontend              │
│    (Routage vers les microservices)    │
└────────────┬───────────────────────────┘
             │
    ┌────────┼──────────┬─────────┬──────┐
    │        │          │         │      │
┌───▼───┐ ┌─▼────┐ ┌──▼─────┐ ┌─▼────┐ │
│ Auth  │ │ Core │ │Scraper │ │Notif.│ │
│ 8001  │ │ 8002 │ │  8003  │ │ 8004 │ │
│       │ │      │ │ ⚡ GHA  │ │      │ │
└───────┘ └──────┘ └────────┘ └──────┘ │
                                   ┌────▼──┐
                                   │ Admin │
                                   │  8005 │
                                   └───────┘
```

**6 microservices** + base de données partagée + message bus

---

## 📦 Services

| Service | Port | Rôle | Remplace |
|---------|------|------|----------|
| **Auth Service** | 8001 | Authentification, JWT, OAuth2 | backend/auth |
| **Core Service** | 8002 | Ventes, lots, favoris, alertes | backend/sales, lots |
| **Scraper Service** | 8003 | **Scraping automatisé** | **GitHub Actions** ⚡ |
| **Notification Service** | 8004 | Emails, notifications push | backend/notifications |
| **Admin Service** | 8005 | Administration, ingestion | backend/admin |
| **API Gateway** | 8000 | Routage centralisé | - |

---

## 🚀 Démarrage Rapide

### Local (Docker)

```bash
# 1. Démarrer tous les microservices
./start-microservices.sh

# 2. Vérifier que tout fonctionne
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8003/health  # Scraper (scheduler actif)

# 3. Accéder à l'application
# Frontend: http://localhost:5173
# API: http://localhost:8000
# RabbitMQ UI: http://localhost:15672 (guest/guest)
```

### Production (Render.com)

```bash
# Déployer via Render Blueprint
# Le fichier render.yaml configure tout automatiquement

1. Connectez-vous à https://dashboard.render.com
2. New → Blueprint
3. Connectez votre repo GitHub
4. Render détecte render.yaml et déploie tous les services
5. Configurez SECRET_KEY dans chaque service (même valeur)
```

Voir [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) pour le guide complet.

---

## ⚡ Scraper Service - Remplace GitHub Actions

Le **Scraper Service** (port 8003) exécute tous les jobs automatiques qui étaient dans GitHub Actions.

### Jobs Automatiques

| Job | Fréquence | Remplace |
|-----|-----------|----------|
| **Scraping des ventes** | Toutes les 15 min | `cron: '*/15 * * * *'` |
| **Découverte des ventes** | Tous les jours à 3h | `cron: '0 3 * * *'` |
| **Mise à jour des prix** | Toutes les minutes | `cron: '* * * * *'` |

### Avantages vs GitHub Actions

| Critère | GitHub Actions | Scraper Service |
|---------|----------------|-----------------|
| Limite de temps | 2000 min/mois | ♾️ Illimité |
| Contrôle | Workflows Git | API REST |
| Logs | Archivés après 90j | Temps réel |
| Debugging | Difficile | Facile |
| Coût | Gratuit (limité) | ~$7/mois |

### API du Scraper

```bash
# Status du scheduler
curl http://localhost:8003/health
# → {"status": "healthy", "scheduler_running": true}

# Liste des jobs configurés
curl http://localhost:8003/api/v1/scraper/jobs

# Déclencher manuellement un job
curl -X POST http://localhost:8003/api/v1/scraper/trigger/scrape_sales

# Voir les logs en temps réel
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

---

## 📚 Documentation

### 🎯 Démarrage

1. **[START_HERE.md](START_HERE.md)** ← **COMMENCER ICI**
   - Guide de démarrage rapide
   - Vue d'ensemble
   - Checklist

2. **[README_MICROSERVICES.md](README_MICROSERVICES.md)**
   - Architecture complète
   - Commandes essentielles
   - Troubleshooting

### 📖 Détails Techniques

3. **[MICROSERVICES_SUMMARY.md](MICROSERVICES_SUMMARY.md)**
   - Résumé exécutif
   - Comparaison avant/après
   - Statistiques

4. **[services/README.md](services/README.md)**
   - Architecture technique
   - Communication inter-services
   - Développement

### 🚀 Déploiement

5. **[MICROSERVICES_DEPLOYMENT.md](MICROSERVICES_DEPLOYMENT.md)**
   - Déploiement Docker local
   - Configuration
   - Monitoring

6. **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)**
   - Déploiement sur Render.com
   - Configuration production
   - Coûts et optimisations

### 🔄 Migration

7. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**
   - Migration depuis le monolithe
   - Mapping des services
   - Tests post-migration

### 📊 Résumé

8. **[TRAVAIL_REALISE.md](TRAVAIL_REALISE.md)**
   - Récapitulatif complet
   - Fichiers créés
   - Statistiques

---

## 🛠️ Technologies

### Backend

- **FastAPI** - Framework web asynchrone
- **SQLAlchemy** - ORM avec support async
- **PostgreSQL** - Base de données
- **Redis** - Cache et queue
- **RabbitMQ** - Message bus
- **Playwright** - Web scraping
- **APScheduler** - Planification de tâches
- **Celery** - Tâches asynchrones
- **Pydantic** - Validation de données

### Frontend

- **React** - Interface utilisateur
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling

### Infrastructure

- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration locale
- **NGINX** - API Gateway
- **Render.com** - Hébergement production

---

## 🏃 Commandes Essentielles

### Développement Local

```bash
# Démarrer
./start-microservices.sh

# Logs
docker-compose -f docker-compose.microservices.yml logs -f

# Arrêter
docker-compose -f docker-compose.microservices.yml down

# Redémarrer un service
docker-compose -f docker-compose.microservices.yml restart scraper-service

# Shell dans un service
docker-compose -f docker-compose.microservices.yml exec core-service bash
```

### Tests

```bash
# Health checks
for port in 8001 8002 8003 8004 8005; do
  echo "Service $port: $(curl -s http://localhost:$port/health)"
done

# Scraper Service
curl http://localhost:8003/api/v1/scraper/jobs
```

### Production (Render)

```bash
# Health checks
curl https://encheres-auth-service.onrender.com/health
curl https://encheres-core-service.onrender.com/health
curl https://encheres-scraper-service.onrender.com/health
```

---

## 🗄️ Base de Données

### Migrations

```bash
# Appliquer les migrations
docker-compose -f docker-compose.microservices.yml exec core-service alembic upgrade head

# Créer une migration
docker-compose -f docker-compose.microservices.yml exec core-service alembic revision --autogenerate -m "Description"
```

### Connexion

```bash
# PostgreSQL local
docker-compose -f docker-compose.microservices.yml exec db psql -U postgres -d encheres

# PostgreSQL Render (via dashboard)
Render Dashboard → encheres-db → Connect → Psql
```

---

## 📊 Monitoring

### Logs

```bash
# Tous les services
docker-compose -f docker-compose.microservices.yml logs -f

# Service spécifique
docker-compose -f docker-compose.microservices.yml logs -f scraper-service

# Production (Render)
Dashboard → Service → Logs
```

### RabbitMQ Management

- **Local:** http://localhost:15672 (guest/guest)
- Surveiller les messages inter-services
- Visualiser les queues

### Health Checks

Tous les services exposent `/health`:

```json
{
  "status": "healthy",
  "scheduler_running": true  // Scraper Service uniquement
}
```

---

## 🔐 Sécurité

### Variables d'Environnement

Ne **jamais** committer ces valeurs :

```env
# .env (local uniquement)
SECRET_KEY=votre-clé-secrète-64-caractères
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
MAIL_PASSWORD=mot-de-passe-application-email
```

### Production

- `SECRET_KEY` : Même valeur pour tous les services
- `COOKIE_SECURE=true` en HTTPS
- CORS limité aux domaines autorisés
- Rate limiting via API Gateway

---

## 💰 Coûts

### Local (Développement)

- **Gratuit** - Tout en Docker local

### Production (Render.com)

| Service | Plan | Coût/mois |
|---------|------|-----------|
| PostgreSQL | Free | $0 |
| Auth Service | Free | $0 |
| Core Service | Free | $0 |
| **Scraper Service** | **Starter** | **$7** |
| Notification Service | Free | $0 |
| Admin Service | Free | $0 |
| Frontend | Free | $0 |
| **Total** | - | **$7/mois** |

**Note:** Le Scraper Service nécessite le plan Starter pour Playwright.

---

## 🤝 Contribution

### Structure du Projet

```
.
├── services/                    # Microservices
│   ├── shared/                  # Bibliothèque commune
│   ├── auth-service/            # Authentification
│   ├── core-service/            # Métier principal
│   ├── scraper-service/         # Scraping (remplace GHA)
│   ├── notification-service/    # Notifications
│   ├── admin-service/           # Administration
│   └── api-gateway/             # NGINX
│
├── frontend/                    # Frontend React
├── backend/                     # Ancien monolithe (archivé)
│
├── docker-compose.microservices.yml
├── render.yaml                  # Config Render.com
└── start-microservices.sh
```

### Ajouter un Service

1. Créer `services/mon-service/`
2. Utiliser `shared/` pour config et utils
3. Ajouter au `docker-compose.microservices.yml`
4. Ajouter au `render.yaml`
5. Configurer les routes dans l'API Gateway

---

## 📝 Changelog

### v2.0.0 - Architecture Microservices (Octobre 2025)

**BREAKING CHANGE:** Migration complète vers microservices

- ✅ 6 microservices créés
- ✅ GitHub Actions remplacé par Scraper Service
- ✅ API Gateway NGINX
- ✅ Message Bus RabbitMQ
- ✅ Documentation exhaustive (7700+ lignes)
- ✅ Script de démarrage automatique
- ✅ Configuration Render.com

### v1.0.0 - Backend Monolithique

- Backend FastAPI monolithique
- GitHub Actions pour scraping
- Déploiement Render.com

---

## 🆘 Support

### Problèmes Courants

Voir [MICROSERVICES_DEPLOYMENT.md](MICROSERVICES_DEPLOYMENT.md) section Troubleshooting.

### Documentation

Consultez les documents dans cet ordre :
1. START_HERE.md
2. README_MICROSERVICES.md
3. Guide spécifique (deployment, migration, etc.)

### Contact

- **Issues GitHub:** [github.com/votre-repo/issues](https://github.com)
- **Documentation:** Dans le dossier `docs/`

---

## 📜 Licence

[À définir]

---

## ✅ Statut du Projet

🟢 **Production Ready**

- ✅ Architecture microservices fonctionnelle
- ✅ Tests d'intégration passants
- ✅ Documentation complète
- ✅ Déployable sur Render.com
- ✅ Scraper Service remplace GitHub Actions
- ✅ Monitoring configuré
- ✅ Sécurité implémentée

---

## 🎉 Remerciements

Construit avec:
- FastAPI
- React
- Docker
- Render.com
- Claude Code

**Le projet est maintenant en architecture microservices moderne !** 🚀
