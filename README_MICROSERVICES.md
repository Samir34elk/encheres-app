# Projet Enchères - Architecture Microservices

## 🎯 Vue d'ensemble

Ce projet a été migré d'une **architecture monolithique** vers une **architecture microservices** complète.

**Changement majeur:** Les workflows GitHub Actions ont été **complètement remplacés** par un service interne de scraping automatisé.

## 🚀 Démarrage Rapide

```bash
# 1. Démarrer tous les microservices
./start-microservices.sh

# 2. Vérifier que tout fonctionne
curl http://localhost:8000/health

# 3. Accéder à l'application
# Frontend: http://localhost:5173
# API Gateway: http://localhost:8000
# RabbitMQ UI: http://localhost:15672 (guest/guest)
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[MICROSERVICES_SUMMARY.md](MICROSERVICES_SUMMARY.md)** | 📖 **COMMENCER ICI** - Résumé complet de la migration |
| **[MICROSERVICES_DEPLOYMENT.md](MICROSERVICES_DEPLOYMENT.md)** | 🚀 Guide de déploiement détaillé |
| **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** | 🔄 Guide de migration depuis le monolithe |
| **[services/README.md](services/README.md)** | 🏗️ Architecture et design des services |

## 🏗️ Architecture

```
┌────────────────────────────────────────┐
│    API Gateway (NGINX) - Port 8000    │
│    Point d'entrée unique               │
└────────────┬───────────────────────────┘
             │
    ┌────────┼──────────┬─────────┬──────┐
    │        │          │         │      │
┌───▼───┐ ┌─▼────┐ ┌──▼─────┐ ┌─▼────┐ │
│ Auth  │ │ Core │ │Scraper │ │Notif.│ │
│ 8001  │ │ 8002 │ │  8003  │ │ 8004 │ │
└───────┘ └──────┘ └────────┘ └──────┘ │
                                   ┌────▼──┐
                                   │ Admin │
                                   │  8005 │
                                   └───────┘
```

## 🎁 Services

| Service | Port | Rôle | Remplace |
|---------|------|------|----------|
| **API Gateway** | 8000 | Routage, rate limiting | - |
| **Auth Service** | 8001 | Authentification | backend/auth |
| **Core Service** | 8002 | Ventes, lots, favoris | backend/sales,lots |
| **Scraper Service** | 8003 | **Scraping automatisé** | **GitHub Actions** ⚡ |
| **Notification Service** | 8004 | Notifications | backend/notifications |
| **Admin Service** | 8005 | Administration | backend/admin |

## ⚡ Point Clé: Scraper Service

Le **Scraper Service** (port 8003) remplace complètement les workflows GitHub Actions.

### Avant (GitHub Actions)

```yaml
# .github/workflows/scheduled-jobs.yml
on:
  schedule:
    - cron: '*/15 * * * *'  # Scraping
    - cron: '0 3 * * *'     # Discovery
    - cron: '* * * * *'     # Price updates
```

### Après (Scraper Service)

Le service utilise **APScheduler** pour exécuter les mêmes tâches en interne:

```python
# services/scraper-service/app/scheduler/jobs.py

# Job 1: Scraping toutes les 15 minutes
scheduler.add_job(scrape_sales_job, interval=15min)

# Job 2: Découverte quotidienne à 3h
scheduler.add_job(discover_sales_job, cron="0 3 * * *")

# Job 3: Prix chaque minute
scheduler.add_job(update_prices_job, interval=1min)
```

### Avantages

- ✅ Pas de limite de temps (GitHub Actions: 2000 min/mois)
- ✅ Logs en temps réel accessibles
- ✅ Contrôle manuel via API REST
- ✅ Infrastructure maîtrisée
- ✅ Debugging facilité

### Contrôle

```bash
# Lister les jobs
curl http://localhost:8003/api/v1/scraper/jobs

# Déclencher manuellement
curl -X POST http://localhost:8003/api/v1/scraper/trigger/scrape_sales

# Voir les logs en temps réel
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

## 📦 Structure du Projet

```
.
├── backend/                          # Ancien backend monolithique (archivé)
├── frontend/                         # Frontend (inchangé)
├── services/                         # 🆕 Nouveau: Microservices
│   ├── shared/                       # Bibliothèque commune
│   ├── auth-service/                 # Service d'authentification
│   ├── core-service/                 # Service métier principal
│   ├── scraper-service/              # ⚡ Remplace GitHub Actions
│   ├── notification-service/         # Service de notifications
│   ├── admin-service/                # Service d'administration
│   ├── api-gateway/                  # Configuration NGINX
│   └── README.md
├── scripts/
│   └── generate_microservices.py     # Script de génération
├── docker-compose.microservices.yml  # Orchestration Docker
├── start-microservices.sh            # Script de démarrage
├── MICROSERVICES_SUMMARY.md          # 📖 LIRE EN PREMIER
├── MICROSERVICES_DEPLOYMENT.md       # Guide de déploiement
└── MIGRATION_GUIDE.md                # Guide de migration
```

## 🔧 Commandes Utiles

### Démarrage

```bash
# Tout démarrer
./start-microservices.sh

# Ou manuellement
docker-compose -f docker-compose.microservices.yml up -d
```

### Monitoring

```bash
# Voir tous les services
docker-compose -f docker-compose.microservices.yml ps

# Logs de tous les services
docker-compose -f docker-compose.microservices.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

### Santé des Services

```bash
# Vérifier tous les services
for port in 8000 8001 8002 8003 8004 8005; do
  echo "Port $port: $(curl -s http://localhost:$port/health)"
done
```

### Arrêt

```bash
# Arrêter tous les services
docker-compose -f docker-compose.microservices.yml down

# Arrêter et supprimer les volumes (⚠️ perte de données)
docker-compose -f docker-compose.microservices.yml down -v
```

## 🌐 URLs des Services

| Service | URL | Description |
|---------|-----|-------------|
| API Gateway | http://localhost:8000 | Point d'entrée principal |
| Auth Service | http://localhost:8001 | Authentification |
| Core Service | http://localhost:8002 | Ventes et lots |
| Scraper Service | http://localhost:8003 | Scraping automatisé |
| Notification Service | http://localhost:8004 | Notifications |
| Admin Service | http://localhost:8005 | Administration |
| RabbitMQ UI | http://localhost:15672 | Management (guest/guest) |
| Frontend | http://localhost:5173 | Application web |

## 🔐 Configuration

Créer un fichier `.env` à la racine:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/encheres

# Security
SECRET_KEY=your-super-secret-key-here

# Scraper (remplace GitHub Actions)
ENABLE_SCHEDULER=true
SCRAPER_INTERVAL_MINUTES=15
ENABLE_PRICE_UPDATES=true

# Email
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
```

## 🧪 Tests

### Test d'Authentification

```bash
# S'inscrire
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"test","password":"test123456"}'

# Se connecter
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123456"
```

### Test du Scraper

```bash
# Status
curl http://localhost:8003/health

# Jobs configurés
curl http://localhost:8003/api/v1/scraper/jobs

# Déclencher manuellement
curl -X POST http://localhost:8003/api/v1/scraper/trigger/scrape_sales
```

## 📊 Monitoring

### RabbitMQ

Interface de management pour surveiller les messages:
- URL: http://localhost:15672
- User: `guest`
- Password: `guest`

### Logs

```bash
# Logs en temps réel de tous les services
docker-compose -f docker-compose.microservices.yml logs -f

# Logs du Scraper uniquement
docker-compose -f docker-compose.microservices.yml logs -f scraper-service

# Logs avec timestamps
docker-compose -f docker-compose.microservices.yml logs -f -t scraper-service
```

## 🆘 Troubleshooting

### Problème: Un service ne démarre pas

```bash
# Voir les logs d'erreur
docker-compose -f docker-compose.microservices.yml logs <service-name>

# Rebuilder le service
docker-compose -f docker-compose.microservices.yml up -d --build <service-name>
```

### Problème: Le Scraper ne lance pas les jobs

```bash
# Vérifier que le scheduler est actif
curl http://localhost:8003/health
# → {"status": "healthy", "scheduler_running": true}

# Vérifier la configuration
docker-compose -f docker-compose.microservices.yml exec scraper-service env | grep ENABLE
# → ENABLE_SCHEDULER=true
```

### Problème: Erreur de connexion base de données

```bash
# Vérifier que PostgreSQL est démarré
docker-compose -f docker-compose.microservices.yml ps db

# Se connecter à PostgreSQL
docker-compose -f docker-compose.microservices.yml exec db psql -U postgres -d encheres
```

## 🔄 Migration depuis le Monolithe

Si vous utilisez encore l'ancien backend monolithique:

1. **Lire** `MIGRATION_GUIDE.md` pour comprendre les changements
2. **Configurer** les variables d'environnement dans `.env`
3. **Démarrer** les microservices avec `./start-microservices.sh`
4. **Tester** tous les endpoints
5. **Désactiver** les workflows GitHub Actions
6. **Supprimer** l'ancien backend (optionnel)

## 📈 Performance

### Ressources Minimales

- CPU: 2 cores (4 recommandés)
- RAM: 4 GB (8 GB recommandés)
- Disk: 10 GB (SSD recommandé)

### Scaling

Pour scaler un service:

```yaml
# docker-compose.microservices.yml
core-service:
  deploy:
    replicas: 3  # 3 instances
```

## ✅ Checklist

- [ ] Docker et Docker Compose installés
- [ ] Fichier `.env` créé et configuré
- [ ] Services démarrés avec `./start-microservices.sh`
- [ ] Tous les health checks passent
- [ ] Frontend accessible sur http://localhost:5173
- [ ] Scraper Service scheduler actif
- [ ] Tests d'authentification OK
- [ ] GitHub Actions désactivé (optionnel)

## 📚 Ressources

- **Documentation complète:** `MICROSERVICES_SUMMARY.md`
- **Guide de déploiement:** `MICROSERVICES_DEPLOYMENT.md`
- **Guide de migration:** `MIGRATION_GUIDE.md`
- **Architecture:** `services/README.md`

## 🎉 Félicitations !

Vous utilisez maintenant une **architecture microservices moderne** avec:
- ✅ 6 microservices indépendants
- ✅ API Gateway centralisé
- ✅ Message Bus pour communication asynchrone
- ✅ Scraping automatisé sans GitHub Actions
- ✅ Scalabilité horizontale
- ✅ Haute disponibilité

**Le projet est prêt pour la production !** 🚀
