# API Gateway

API Gateway NGINX qui route les requêtes vers les microservices.

## 📁 Fichiers de configuration

- `nginx.conf` - Configuration pour déploiement local (Docker Compose)
- `nginx.render.conf` - Configuration pour déploiement Render (sous-domaines publics)
- `Dockerfile` - Image Docker pour le déploiement

## 🔄 Configurations disponibles

### Configuration Locale (`nginx.conf`)
Utilise les noms de service Docker internes:
- `auth-service:8001`
- `core-service:8002`
- `scraper-service:8003`
- etc.

### Configuration Render (`nginx.render.conf`)
Utilise les sous-domaines publics:
- `auth.samirdev.site`
- `core.samirdev.site`
- `scraper.samirdev.site`
- `notifications.samirdev.site`
- `admin.samirdev.site`

## 🧪 Test local

Pour tester la configuration Render en local:

```bash
# Copier la config Render
cp nginx.render.conf nginx.conf

# Build et lancer
docker build -t api-gateway .
docker run -p 8000:80 api-gateway

# Tester
curl http://localhost:8000/health
curl http://localhost:8000/
```

## 🚀 Déploiement sur Render

### Option 1: Via Dashboard Render

1. Aller sur https://dashboard.render.com/
2. New → Web Service
3. Connect GitHub repository
4. Configuration:
   - **Name**: `encheres-api-gateway`
   - **Region**: Frankfurt (ou proche de tes services)
   - **Branch**: master
   - **Runtime**: Docker
   - **Dockerfile Path**: `./services/api-gateway/Dockerfile`
   - **Docker Context**: `./services/api-gateway`
   - **Plan**: Free

5. Variables d'environnement (aucune requise pour l'instant)

6. Advanced:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes

### Option 2: Via Render Blueprint (render.yaml)

Ajouter dans `render.yaml`:

```yaml
services:
  - type: web
    name: encheres-api-gateway
    runtime: docker
    dockerfilePath: ./services/api-gateway/Dockerfile
    dockerContext: ./services/api-gateway
    plan: free
    region: frankfurt
    healthCheckPath: /health
    autoDeploy: true
```

## 📝 Notes importantes

⚠️ **Avant le déploiement sur Render**, copier la config Render:

```bash
cd services/api-gateway
cp nginx.render.conf nginx.conf
git add .
git commit -m "feat: Configure API Gateway for Render deployment"
git push
```

## 🔍 Endpoints

- `GET /` - Informations sur le gateway
- `GET /health` - Health check
- `/api/v1/auth/*` → auth.samirdev.site
- `/api/v1/sales/*` → core.samirdev.site
- `/api/v1/lots/*` → core.samirdev.site
- `/api/v1/favorites/*` → core.samirdev.site
- `/api/v1/alerts/*` → core.samirdev.site
- `/api/v1/scraper/*` → scraper.samirdev.site
- `/api/v1/notifications/*` → notifications.samirdev.site
- `/api/v1/admin/*` → admin.samirdev.site
- `/api/v1/ingestion/*` → admin.samirdev.site

## 🛡️ Sécurité

- CORS activé pour tous les domaines
- Rate limiting configuré:
  - Auth: 5 req/min
  - API: 60 req/min
- Headers CRON_SECRET passés aux services scraper et admin
