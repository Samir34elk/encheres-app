# Guide de Déploiement sur Render.com

## 🎯 Vue d'Ensemble

Ce guide explique comment déployer l'architecture microservices sur Render.com.

**Point clé:** Le Scraper Service remplace GitHub Actions - tout est autonome !

---

## 📋 Services à Déployer

| Service | Plan | URL | Description |
|---------|------|-----|-------------|
| **encheres-db** | Free | - | Base de données PostgreSQL |
| **encheres-auth-service** | Free | encheres-auth-service.onrender.com | Authentification |
| **encheres-core-service** | Free | encheres-core-service.onrender.com | Ventes, lots |
| **encheres-scraper-service** | **Starter** | encheres-scraper-service.onrender.com | **Remplace GitHub Actions** |
| **encheres-notification-service** | Free | encheres-notification-service.onrender.com | Notifications |
| **encheres-admin-service** | Free | encheres-admin-service.onrender.com | Administration |
| **encheres-frontend** | Free | encheres-frontend.onrender.com | Frontend |

**Total:** 7 services (1 base de données + 5 services web + 1 frontend)

---

## 🚀 Méthode 1: Déploiement Automatique (Recommandé)

### Étape 1: Préparer le Blueprint

Le fichier `render.yaml` est déjà configuré pour déployer tous les services.

### Étape 2: Déployer via Render Dashboard

1. **Connectez-vous** à https://dashboard.render.com

2. **Créer un Blueprint**
   - Cliquez sur "New" → "Blueprint"
   - Connectez votre repo GitHub
   - Sélectionnez le dépôt `encheres-app`
   - Render détectera automatiquement `render.yaml`

3. **Configurer les Variables d'Environnement**

   Render va créer tous les services. Vous devez configurer manuellement :

   **Pour TOUS les services (Auth, Core, Scraper, Notification, Admin):**
   - `SECRET_KEY` : Utiliser la même clé pour tous
     - Générer avec : `openssl rand -base64 64`
     - Aller dans chaque service → Environment → Ajouter `SECRET_KEY`

   **Pour Notification Service uniquement:**
   - `MAIL_USERNAME` : Votre email SMTP
   - `MAIL_PASSWORD` : Mot de passe d'application SMTP

4. **Lancer le Déploiement**
   - Cliquez sur "Apply"
   - Render va :
     1. Créer la base de données
     2. Déployer les 5 microservices
     3. Déployer le frontend
     4. Configurer automatiquement les URLs inter-services

5. **Attendre le Déploiement**
   - Base de données : ~2-3 minutes
   - Services : ~5-10 minutes chacun (Scraper plus long: ~15 min avec Playwright)
   - Frontend : ~3-5 minutes

---

## 🛠️ Méthode 2: Déploiement Manuel

### 1. Créer la Base de Données

```
Dashboard → New → PostgreSQL
- Name: encheres-db
- Region: Frankfurt
- Plan: Free
```

### 2. Déployer Auth Service

```
Dashboard → New → Web Service
- Name: encheres-auth-service
- Environment: Docker
- Dockerfile Path: ./services/auth-service/Dockerfile
- Docker Context: ./services
- Region: Frankfurt
- Plan: Free

Environment Variables:
- DATABASE_URL: [Lier à encheres-db]
- DATABASE_URL_SYNC: [Lier à encheres-db]
- SECRET_KEY: [Générer]
- PORT: 8001
- DEBUG: false
```

### 3. Déployer Core Service

```
Dashboard → New → Web Service
- Name: encheres-core-service
- Environment: Docker
- Dockerfile Path: ./services/core-service/Dockerfile
- Docker Context: ./services
- Region: Frankfurt
- Plan: Free

Environment Variables:
- DATABASE_URL: [Lier à encheres-db]
- DATABASE_URL_SYNC: [Lier à encheres-db]
- SECRET_KEY: [Même que Auth Service]
- AUTH_SERVICE_URL: https://encheres-auth-service.onrender.com
- PORT: 8002
- DEBUG: false
```

### 4. Déployer Scraper Service ⚡

```
Dashboard → New → Web Service
- Name: encheres-scraper-service
- Environment: Docker
- Dockerfile Path: ./services/scraper-service/Dockerfile
- Docker Context: ./services
- Region: Frankfurt
- Plan: STARTER (important pour Playwright)

Environment Variables:
- DATABASE_URL: [Lier à encheres-db]
- DATABASE_URL_SYNC: [Lier à encheres-db]
- SECRET_KEY: [Même que les autres]
- CORE_SERVICE_URL: https://encheres-core-service.onrender.com
- ENABLE_SCHEDULER: true
- SCRAPER_INTERVAL_MINUTES: 15
- ENABLE_PRICE_UPDATES: true
- PORT: 8003
- DEBUG: false
```

### 5. Déployer Notification Service

```
Dashboard → New → Web Service
- Name: encheres-notification-service
- Environment: Docker
- Dockerfile Path: ./services/notification-service/Dockerfile
- Docker Context: ./services
- Region: Frankfurt
- Plan: Free

Environment Variables:
- DATABASE_URL: [Lier à encheres-db]
- SECRET_KEY: [Même que les autres]
- MAIL_USERNAME: [Votre email]
- MAIL_PASSWORD: [Mot de passe app]
- PORT: 8004
```

### 6. Déployer Admin Service

```
Dashboard → New → Web Service
- Name: encheres-admin-service
- Environment: Docker
- Dockerfile Path: ./services/admin-service/Dockerfile
- Docker Context: ./services
- Region: Frankfurt
- Plan: Free

Environment Variables:
- DATABASE_URL: [Lier à encheres-db]
- SECRET_KEY: [Même que les autres]
- AUTH_SERVICE_URL: https://encheres-auth-service.onrender.com
- CORE_SERVICE_URL: https://encheres-core-service.onrender.com
- PORT: 8005
```

### 7. Déployer Frontend

```
Dashboard → New → Static Site
- Name: encheres-frontend
- Build Command: cd frontend && npm install && npm run build
- Publish Directory: frontend/dist

Environment Variables:
- VITE_API_URL: https://encheres-auth-service.onrender.com/api/v1
- VITE_CORE_SERVICE_URL: https://encheres-core-service.onrender.com/api/v1
```

---

## ✅ Vérification du Déploiement

### 1. Health Checks

Vérifiez que tous les services sont "healthy" :

```bash
# Auth Service
curl https://encheres-auth-service.onrender.com/health

# Core Service
curl https://encheres-core-service.onrender.com/health

# Scraper Service (important!)
curl https://encheres-scraper-service.onrender.com/health
# Devrait retourner: {"status": "healthy", "scheduler_running": true}

# Notification Service
curl https://encheres-notification-service.onrender.com/health

# Admin Service
curl https://encheres-admin-service.onrender.com/health
```

### 2. Vérifier le Scraper Service

**C'est le service critique qui remplace GitHub Actions !**

```bash
# Vérifier que le scheduler est actif
curl https://encheres-scraper-service.onrender.com/

# Devrait retourner:
# {
#   "service": "scraper-service",
#   "version": "1.0.0",
#   "status": "running",
#   "replaces": "GitHub Actions scheduled-jobs.yml",
#   "scheduler_enabled": true
# }

# Vérifier les jobs configurés
curl https://encheres-scraper-service.onrender.com/api/v1/scraper/jobs
```

### 3. Consulter les Logs

Dans le dashboard Render, pour chaque service :

**Scraper Service (important):**
```
Dashboard → encheres-scraper-service → Logs

Vous devriez voir:
============================================================
🚀 Starting Internal Scheduler
   REPLACES: GitHub Actions (.github/workflows/scheduled-jobs.yml)
============================================================
✓ Job 1: Scrape sales every 15 minutes
✓ Job 2: Discover sales daily at 3:00 AM
✓ Job 3: Update favorite prices every minute
============================================================
✅ Scheduler started successfully!
============================================================
```

### 4. Tester le Frontend

Accédez à : https://encheres-frontend.onrender.com

Testez :
- Inscription / Connexion
- Navigation
- Fonctionnalités principales

---

## ⚙️ Configuration Post-Déploiement

### 1. Appliquer les Migrations de Base de Données

Connectez-vous à n'importe quel service et lancez :

```bash
# Via Render Shell (dans un service)
alembic upgrade head
```

Ou via Render Dashboard :
```
Service → Shell → Lancer commande
```

### 2. Configurer le SECRET_KEY Partagé

**Important:** Tous les services doivent utiliser la même `SECRET_KEY` pour partager les tokens JWT.

```bash
# Générer une clé
openssl rand -base64 64

# Copier cette clé dans TOUS les services:
# - encheres-auth-service
# - encheres-core-service
# - encheres-scraper-service
# - encheres-notification-service
# - encheres-admin-service
```

### 3. Configurer l'Email (Notification Service)

Pour Gmail:
1. Activer l'authentification à deux facteurs
2. Créer un "mot de passe d'application"
3. Utiliser ce mot de passe dans `MAIL_PASSWORD`

Variables:
```
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=mot-de-passe-app
MAIL_FROM=noreply@encheres.com
MAIL_SERVER=smtp.gmail.com
```

---

## 🔍 Surveillance et Maintenance

### Logs en Temps Réel

Dashboard → Service → Logs

**Scraper Service (à surveiller):**
- Vérifier que les jobs s'exécutent
- Surveiller les erreurs de scraping
- Vérifier que Playwright fonctionne

### Métriques

Dashboard → Service → Metrics

Surveiller:
- CPU usage (surtout Scraper Service)
- Memory usage
- Request count
- Response times

### Alertes

Configurer des alertes si :
- Un service tombe
- Le Scraper Service ne répond plus
- Erreurs de base de données

---

## 💰 Coûts

### Plan Free

- **Base de données**: Free (1 GB, 90 jours max inactivité)
- **Services Web (Free tier)**: 4 services × 0$ = 0$
  - Auth Service
  - Core Service
  - Notification Service
  - Admin Service
- **Frontend (Static)**: Free

### Plan Payant Nécessaire

- **Scraper Service**: **Starter Plan** (~$7/mois)
  - Nécessaire pour Playwright (besoin de plus de RAM)
  - Reste actif en permanence (pas de sleep)
  - Exécute les jobs toutes les 15 min

**Total mensuel: ~$7/mois** (au lieu de dépendre de GitHub Actions)

### Comparaison

| Solution | Coût | Limites |
|----------|------|---------|
| **GitHub Actions** | Gratuit | 2000 min/mois, complexe à debugger |
| **Scraper Service (Render)** | $7/mois | Illimité, contrôle total |

---

## 🚨 Problèmes Courants

### 1. Scraper Service ne démarre pas

**Symptôme:** Health check échoue

**Solution:**
```bash
# Vérifier les logs
Dashboard → encheres-scraper-service → Logs

# Erreur courante: Plan trop petit
# → Passer au plan "Starter"

# Erreur Playwright
# → Vérifier que Dockerfile installe les dépendances système
```

### 2. Services ne peuvent pas communiquer

**Symptôme:** Erreurs 503 "Service unavailable"

**Solution:**
```bash
# Vérifier les URLs dans environment variables
AUTH_SERVICE_URL=https://encheres-auth-service.onrender.com
CORE_SERVICE_URL=https://encheres-core-service.onrender.com

# Vérifier que les services sont démarrés
curl https://encheres-core-service.onrender.com/health
```

### 3. Jobs du Scraper ne s'exécutent pas

**Symptôme:** Pas d'activité dans les logs

**Solution:**
```bash
# Vérifier ENABLE_SCHEDULER
Dashboard → encheres-scraper-service → Environment
ENABLE_SCHEDULER=true (doit être une string "true")

# Redémarrer le service
Dashboard → encheres-scraper-service → Manual Deploy
```

### 4. Frontend ne se connecte pas à l'API

**Symptôme:** Erreurs CORS ou 404

**Solution:**
```bash
# Vérifier VITE_API_URL
Dashboard → encheres-frontend → Environment
VITE_API_URL=https://encheres-auth-service.onrender.com/api/v1

# Rebuilder le frontend
Dashboard → encheres-frontend → Manual Deploy
```

---

## 🎯 Migration depuis l'Ancien Backend

### 1. Tester les Nouveaux Services

Avant de supprimer l'ancien backend :

```bash
# Comparer les endpoints
curl https://encheres-backend.onrender.com/health
curl https://encheres-auth-service.onrender.com/health
curl https://encheres-core-service.onrender.com/health
```

### 2. Basculer le Frontend

```bash
# Mettre à jour VITE_API_URL dans le frontend
Avant: https://encheres-backend.onrender.com/api/v1
Après: https://encheres-auth-service.onrender.com/api/v1
```

### 3. Vérifier que Tout Fonctionne

- Tester l'authentification
- Tester les principales fonctionnalités
- Vérifier les jobs du Scraper Service

### 4. Supprimer l'Ancien Backend

Une fois tout validé :

```
Dashboard → encheres-backend → Settings → Delete Service
```

---

## 📚 Ressources

- **Render Documentation**: https://render.com/docs
- **Blueprint Spec**: https://render.com/docs/blueprint-spec
- **Docker on Render**: https://render.com/docs/docker
- **Environment Variables**: https://render.com/docs/environment-variables

---

## ✅ Checklist de Déploiement

- [ ] Base de données créée (encheres-db)
- [ ] Auth Service déployé et healthy
- [ ] Core Service déployé et healthy
- [ ] Scraper Service déployé avec plan STARTER
- [ ] Scraper Service scheduler actif (vérifier logs)
- [ ] Notification Service déployé
- [ ] Admin Service déployé
- [ ] Frontend déployé
- [ ] SECRET_KEY partagée configurée sur tous les services
- [ ] MAIL_USERNAME/PASSWORD configurés
- [ ] Migrations de base de données appliquées
- [ ] Health checks passent pour tous les services
- [ ] Jobs du Scraper s'exécutent (vérifier après 15 min)
- [ ] Frontend fonctionne et communique avec les services
- [ ] GitHub Actions désactivé (optionnel)
- [ ] Ancien backend supprimé (après validation)

---

## 🎉 Félicitations !

Votre architecture microservices est déployée sur Render !

**Points clés:**
- ✅ 5 microservices indépendants
- ✅ Scraper Service remplace GitHub Actions
- ✅ Pas de limite de temps d'exécution
- ✅ Contrôle total via API
- ✅ Logs en temps réel
- ✅ Scalabilité assurée

**Le projet est en production !** 🚀
