# Rapport de Diagnostic et Solutions - Projet Enchères

**Date :** 2025-10-20
**Environnement :** Render (Plan Gratuit)
**Stack :** FastAPI (Backend) + React/Vite (Frontend) + PostgreSQL

---

## 🔍 Problèmes Identifiés

### 1. ❌ Jobs Planifiés Non Fiables sur Render Free

**Description :**
Le backend utilise APScheduler pour exécuter des tâches planifiées :
- `scrape_sales_job` : Scraping des ventes toutes les 15 minutes
- `discover_sales_job` : Découverte quotidienne des ventes à 3h00

**Fichier concerné :** `backend/app/services/scheduler.py:49-70`

**Problème :**
Sur le plan gratuit de Render :
- Les instances web s'arrêtent après **15 minutes d'inactivité**
- Les jobs planifiés ne s'exécuteront PAS si l'instance est inactive
- Même avec un ping externe, les instances gratuites ont des limitations

**Impact :**
- Les données ne sont pas mises à jour automatiquement
- Les utilisateurs ne voient pas les nouvelles ventes
- Les alertes ne sont pas déclenchées

---

### 2. ❌ Erreur 404 "Not Found" à la Déconnexion (Frontend)

**Description :**
Lors de la déconnexion, le frontend redirige vers `/login` via `window.location.href`, ce qui provoque une erreur 404 sur Render.

**Fichier concerné :** `frontend/src/stores/authStore.ts:63`

**Problème :**
- Render sert les sites statiques sans configuration SPA par défaut
- Le fichier `static.json` existe mais Render ne le lit pas
- Il manque un fichier `_redirects` pour rediriger toutes les routes vers `index.html`

**Impact :**
- Les utilisateurs voient une page 404 lors de la déconnexion
- Les liens directs vers des routes (/login, /dashboard, etc.) ne fonctionnent pas
- Navigation impossible après un refresh de page

---

### 3. ⚠️ Configuration CORS et Cookies en Production

**Fichier concerné :** `backend/app/core/config.py:114-119`

**Observations :**
- Les cookies sont configurés avec `SameSite=none` et `Secure=True` en production
- Les origines CORS doivent inclure l'URL exacte du frontend Render

**Actuel dans render.yaml :**
```yaml
BACKEND_CORS_ORIGINS: '["https://encheres-frontend.onrender.com"]'
```

---

## ✅ Solutions Proposées

### Solution 1 : Alternatives pour le Scheduling

#### Option A : GitHub Actions (Recommandé ✨)
Utiliser GitHub Actions pour exécuter les jobs planifiés via des appels API.

**Avantages :**
- Gratuit et fiable
- S'exécute même si Render est en veille
- Historique des exécutions
- Notifications en cas d'échec

**Implémentation :**

1. Créer des endpoints API pour déclencher les jobs :

```python
# backend/app/api/v1/endpoints/scheduler.py
from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter()

CRON_SECRET = settings.CRON_SECRET  # À ajouter dans config

async def verify_cron_secret(x_cron_secret: str = Header(None)):
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

@router.post("/trigger-scraping")
async def trigger_scraping(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """Endpoint pour déclencher le scraping via GitHub Actions"""
    batch = BatchAuctionScraper(db)
    summary = await batch.run()
    return {"status": "success", "summary": summary}

@router.post("/trigger-discovery")
async def trigger_discovery(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """Endpoint pour déclencher la découverte via GitHub Actions"""
    service = SaleDiscoveryService()
    sales = await service.fetch_sales()
    created, updated = await service.sync_with_database(db, sales)
    return {
        "status": "success",
        "total": len(sales),
        "created": created,
        "updated": updated
    }
```

2. Créer le workflow GitHub Actions :

```yaml
# .github/workflows/scheduled-jobs.yml
name: Scheduled Jobs

on:
  schedule:
    # Scraping toutes les 15 minutes
    - cron: '*/15 * * * *'
    # Découverte quotidienne à 3h00 UTC
    - cron: '0 3 * * *'
  workflow_dispatch:  # Permet l'exécution manuelle

jobs:
  scrape-sales:
    if: github.event.schedule == '*/15 * * * *'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Scraping
        run: |
          curl -X POST \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET }}" \
            https://encheres-backend.onrender.com/api/v1/scheduler/trigger-scraping

  discover-sales:
    if: github.event.schedule == '0 3 * * *'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Discovery
        run: |
          curl -X POST \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET }}" \
            https://encheres-backend.onrender.com/api/v1/scheduler/trigger-discovery
```

#### Option B : Service Externe de Cron
Utiliser un service comme **cron-job.org** ou **EasyCron** (gratuit).

#### Option C : Render Cron Jobs (Payant)
Render propose des Cron Jobs mais uniquement sur les plans payants.

---

### Solution 2 : Corriger le 404 Frontend

#### Créer un fichier _redirects pour Render

```bash
# frontend/public/_redirects
/*    /index.html   200
```

Ce fichier sera copié dans `dist/` lors du build et indiquera à Render de rediriger toutes les routes vers index.html.

#### Alternative : Modifier le routing React

Au lieu de `window.location.href = '/login'`, utiliser `navigate('/login')` :

```typescript
// frontend/src/stores/authStore.ts
import { useNavigate } from 'react-router-dom'

// Dans la fonction logout :
logout: async () => {
  try {
    await api.post('/auth/logout')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
    // Utiliser navigate au lieu de window.location
    // Note: nécessite de restructurer le store pour avoir accès à navigate
  }
}
```

**Note :** La première solution (fichier _redirects) est plus simple et corrige tous les cas.

---

### Solution 3 : Vérifier la Configuration CORS

S'assurer que les URLs correspondent exactement :
- Frontend : `https://encheres-frontend.onrender.com`
- Backend : `https://encheres-backend.onrender.com`

---

## 🧪 Tests à Effectuer

### Tests Locaux
```bash
# 1. Tester le backend localement
cd backend
python -m pytest -v

# 2. Tester le frontend localement
cd frontend
npm run test

# 3. Tester le flow d'authentification complet
npm run dev
# Puis tester : connexion → navigation → déconnexion
```

### Tests en Production

1. **Test d'authentification :**
   - Connexion ✓
   - Navigation entre pages ✓
   - Déconnexion ✓
   - Accès direct aux routes (refresh) ✓

2. **Test des endpoints de scheduling :**
   ```bash
   curl -X POST \
     -H "X-Cron-Secret: YOUR_SECRET" \
     https://encheres-backend.onrender.com/api/v1/scheduler/trigger-scraping
   ```

3. **Vérifier les logs Render :**
   - Erreurs CORS
   - Erreurs de cookies
   - Erreurs de base de données

---

## 📋 Plan d'Action

### Phase 1 : Corrections Immédiates (30 min)
- [ ] Créer le fichier `frontend/public/_redirects`
- [ ] Tester le build et déployer
- [ ] Vérifier que la déconnexion fonctionne

### Phase 2 : Mise en Place du Scheduling (1h)
- [ ] Créer les endpoints API de scheduling
- [ ] Ajouter la sécurité (secret key)
- [ ] Créer le workflow GitHub Actions
- [ ] Tester manuellement les endpoints
- [ ] Activer le workflow et monitorer

### Phase 3 : Tests et Validation (30 min)
- [ ] Tester tous les flows utilisateurs
- [ ] Vérifier les logs
- [ ] Documenter les changements

### Phase 4 : Améliorations Optionnelles
- [ ] Ajouter un endpoint de health check pour les jobs
- [ ] Mettre en place des alertes (email/webhook) en cas d'échec
- [ ] Logger les exécutions dans la base de données
- [ ] Créer un dashboard admin pour voir l'historique des jobs

---

## 📊 Monitoring et Observabilité

### Ajouts Recommandés

1. **Endpoint de statut des jobs :**
```python
@router.get("/jobs/status")
async def get_jobs_status(db: AsyncSession = Depends(get_db)):
    # Retourner la date de dernière exécution, statut, etc.
    pass
```

2. **Logs structurés :**
   - Utiliser un service comme Logtail ou Papertrail
   - Render gratuit conserve les logs pendant 7 jours

3. **Alertes :**
   - Configurer des webhooks Discord/Slack pour les échecs
   - Email de notification

---

## 🔐 Sécurité

### Points à Vérifier

1. **Secret pour les endpoints cron :**
   - Générer un secret fort : `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - L'ajouter dans les secrets GitHub et Render

2. **Rate limiting sur les endpoints :**
   - Déjà en place via `app.core.rate_limit`
   - Vérifier les limites

3. **HTTPS obligatoire :**
   - Déjà configuré via Render

---

## 📝 Notes Supplémentaires

### Limitations Render Free Plan
- 512 MB RAM
- Instance s'arrête après 15 min d'inactivité
- 750 heures/mois gratuites
- Pas de cron jobs natifs
- Connexions DB limitées

### Alternatives à Considérer (Futur)
- **Railway** : Plan gratuit plus généreux
- **Fly.io** : Meilleure performance, plan gratuit correct
- **Vercel** (frontend) + **Render** (backend)
- **Self-hosting** sur VPS (Hetzner, DigitalOcean)

---

## ✅ Résumé

**Problèmes critiques :**
1. ✅ Jobs planifiés → Solution GitHub Actions
2. ✅ Frontend 404 → Fichier _redirects

**Prochaines étapes :**
1. Implémenter le fichier _redirects
2. Créer les endpoints de scheduling
3. Configurer GitHub Actions
4. Tester en production

---

**Généré le :** 2025-10-20
**Auteur :** Claude Code
**Version :** 1.0
