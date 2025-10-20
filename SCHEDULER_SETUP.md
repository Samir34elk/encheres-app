# Configuration du Scheduler avec GitHub Actions

Ce guide explique comment configurer les jobs planifiés pour contourner les limitations du plan gratuit de Render.

## 🎯 Objectif

Sur le plan gratuit de Render, les instances web s'arrêtent après 15 minutes d'inactivité. Cela empêche les jobs planifiés internes (APScheduler) de s'exécuter de manière fiable et rend le scraping Playwright trop coûteux côté serveur.

**Solution :** Déporter tout le scraping dans GitHub Actions. Un worker GitHub lance Playwright, collecte les données et les pousse vers l'API d'ingestion (`/api/v1/ingestion/*`). Le backend se contente d'ingérer les données déjà scrapées.

---

## 📋 Étape 1 : Générer un Secret CRON

Le secret protège les endpoints de scheduling contre les accès non autorisés.

```bash
# Générer un secret fort
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important :** Sauvegardez ce secret, vous en aurez besoin pour les étapes suivantes.

---

## 📋 Étape 2 : Configurer Render

### 2.1 Ajouter la variable d'environnement

1. Connectez-vous à [Render Dashboard](https://dashboard.render.com/)
2. Sélectionnez votre service backend (`encheres-backend`)
3. Allez dans **Environment**
4. Ajoutez une nouvelle variable :
   - **Key :** `CRON_SECRET`
   - **Value :** Le secret généré à l'étape 1
5. Cliquez sur **Save Changes**

Le service redémarrera automatiquement.

### 2.2 Mettre à jour render.yaml (optionnel)

Vous pouvez aussi ajouter ceci dans `render.yaml` pour les futurs déploiements :

```yaml
services:
  - type: web
    name: encheres-backend
    envVars:
      # ... autres variables ...
      - key: CRON_SECRET
        sync: false  # Ne pas synchroniser, garder la valeur actuelle
```

---

## 📋 Étape 3 : Configurer GitHub Secrets

1. Allez dans les **Settings** de votre repository GitHub
2. Cliquez sur **Secrets and variables** > **Actions**
3. Cliquez sur **New repository secret**
4. Ajoutez :
   - **Name :** `CRON_SECRET`
   - **Value :** Le même secret qu'à l'étape 1
5. Cliquez sur **Add secret**

---

## 📋 Étape 4 : Déployer les Changements

### 4.1 Vérifier les fichiers

Les éléments clés du nouveau pipeline :

- ✅ `backend/app/api/v1/endpoints/ingestion.py` — endpoints d'ingestion sécurisés
- ✅ `backend/app/services/ingestion.py` — services de mise à jour BD
- ✅ `.github/workflows/scheduled-jobs.yml` — workflow GitHub Actions
- ✅ `scripts/gha_scrape_and_ingest.py` — worker Playwright côté GitHub
- ✅ `scripts/requirements-scraper.txt` — dépendances minimales

### 4.2 Commit et push

```bash
git add .
git commit -m "feat: Add external scheduler endpoints and GitHub Actions workflow

- Add scheduler API endpoints with secret authentication
- Create GitHub Actions workflow for scheduled jobs
- Fix frontend 404 errors with _redirects file
- Add CRON_SECRET configuration

This allows scheduled jobs to run reliably on Render Free tier."

git push origin master
```

### 4.3 Vérifier le déploiement

1. Vérifiez que Render a redéployé le backend
2. Vérifiez que le frontend a été rebuil (le fichier `_redirects` doit être dans `dist/`)

---

## 📋 Étape 5 : Tester

### 5.1 Test local (optionnel)

```bash
# Démarrer le backend localement
cd backend
export CRON_SECRET="test-secret-for-local-dev"
uvicorn app.main:app --reload

# Dans le dossier racine, créer un virtualenv puis lancer le worker
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements-scraper.txt
export API_BASE_URL="http://localhost:8000/api/v1"
python scripts/gha_scrape_and_ingest.py --mode both --max-sales 2
```

### 5.2 Test en production

```bash
# Remplacer YOUR_SECRET par votre vrai secret
export CRON_SECRET="YOUR_SECRET"
python scripts/gha_scrape_and_ingest.py --mode discover --max-pages 3 --api-base https://encheres-backend.onrender.com/api/v1
python scripts/gha_scrape_and_ingest.py --mode scrape --max-sales 10 --api-base https://encheres-backend.onrender.com/api/v1
```

Vous devriez voir :
- ✅ Découverte des ventes poussée via `/ingestion/sales-metadata`
- ✅ Lots ingérés via `/ingestion/sales`

---

## 📋 Étape 6 : Activer GitHub Actions

### 6.1 Vérifier le workflow

1. Allez dans l'onglet **Actions** du repository
2. Le workflow "Scheduled Jobs" se découpe désormais en :
   - **prepare-sales** : recense les ventes actives, ingère les métadonnées et produit la matrice de ventes à traiter.
   - **scrape-sales** : job matriciel (1 vente par runner) exécutant `scripts/gha_scrape_and_ingest.py --mode scrape --sale <n>`.
   - **discover-sales** : balayage complet (plusieurs pages) lancé chaque nuit à 03:00 UTC.
3. Le planning reste identique :
   - Scraping matriciel toutes les 15 minutes (prepare + matrix)
   - Découverte complète quotidienne à 3h00 UTC

### 6.2 Test manuel

1. Dans l'onglet **Actions**, cliquez sur "Scheduled Jobs"
2. Cliquez sur **Run workflow**
3. Choisissez `scraping`, `discovery` ou `both`
4. Le workflow lancera le script correspondant et poussera les données via les endpoints d'ingestion

Vous verrez les logs en temps réel.

---

## 🔍 Monitoring

### Vérifier l'historique des jobs

Allez dans **Actions** > **Scheduled Jobs** pour visualiser :
- ✅ Les lancements du worker (Playwright + ingestion)
- ⏱️ Le temps passé et la taille des payloads
- ❌ Les erreurs éventuelles (secret manquant, parsing impossible, etc.)

### Vérifier les logs Render

1. Connectez-vous à Render Dashboard
2. Sélectionnez votre service backend
3. Allez dans **Logs**
4. Recherchez : `"Scraping job triggered via API endpoint"`

### Endpoint de statut

Vérifiez le statut des jobs :

```bash
curl https://encheres-backend.onrender.com/api/v1/scheduler/jobs-status
```

---

## 🚨 Troubleshooting

### Les jobs ne s'exécutent pas

1. **Vérifier le secret GitHub :** les logs du workflow indiquent "Invalid or missing cron secret" si `CRON_SECRET` est absent.
2. **Vérifier la variable Render :** `CRON_SECRET` doit être défini dans l'environnement Render.
3. **Playerwright échoue à se lancer :** vérifiez que l'étape `python -m playwright install --with-deps chromium` passe bien (dépendances système).
4. **Ingestion en erreur 503 :** le backend doit exposer `/api/v1/ingestion/*` (déployez la dernière version).

### Erreur 401 Unauthorized

Le secret ne correspond pas. Vérifiez que :
- Le secret GitHub est correct
- La variable d'environnement Render est définie
- Le backend a été redéployé après l'ajout de la variable

### Erreur 500 Internal Server Error

Regardez les logs Render pour voir l'erreur détaillée :
- Dashboard > Service > Logs

Causes possibles :
- Base de données inaccessible
- Erreur dans le code de scraping
- Timeout

---

## 📊 Ajustements du Planning

Pour modifier la fréquence des jobs, éditez `.github/workflows/scheduled-jobs.yml` :

```yaml
on:
  schedule:
    # Scraping : changer la fréquence ici
    - cron: '*/30 * * * *'  # Toutes les 30 minutes au lieu de 15

    # Discovery : changer l'heure ici
    - cron: '0 2 * * *'  # 2h00 UTC au lieu de 3h00
```

**Syntaxe cron :**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Jour de la semaine (0-6, dimanche = 0)
│ │ │ └───── Mois (1-12)
│ │ └─────── Jour du mois (1-31)
│ └───────── Heure (0-23)
└─────────── Minute (0-59)
```

Exemples :
- `0 * * * *` : Toutes les heures
- `0 */6 * * *` : Toutes les 6 heures
- `0 0 * * *` : Tous les jours à minuit
- `0 0 * * 1` : Tous les lundis à minuit

---

## 🎉 Résumé

Une fois configuré, vous avez :

✅ **Jobs planifiés fiables** via GitHub Actions
✅ **Frontend sans erreurs 404** grâce au fichier `_redirects`
✅ **Sécurité** avec authentification par secret
✅ **Monitoring** via GitHub Actions logs et Render logs
✅ **Flexibilité** pour ajuster les plannings

Le système fonctionne même si l'instance Render est en veille. GitHub Actions réveillera l'instance au besoin.

---

## 🔗 Ressources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Render Documentation](https://render.com/docs)
- [Cron Syntax](https://crontab.guru/)
- [Render Free Tier Limitations](https://render.com/docs/free)

---

**Dernière mise à jour :** 2025-10-20
