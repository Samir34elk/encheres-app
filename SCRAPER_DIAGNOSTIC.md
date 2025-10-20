# 🔍 Diagnostic - Scraper retourne 0 ventes

**Problème :** Les jobs s'exécutent correctement mais ne trouvent aucune vente.

---

## 🎯 Analyse du Problème

### Ce qui fonctionne ✅
- Endpoints de scheduler accessibles
- Authentification par secret fonctionne
- Jobs s'exécutent sans erreur
- Database accessible

### Ce qui ne fonctionne pas ❌
- **Discovery job** : Retourne 0 ventes trouvées
- **Scraping job** : Retourne 0 ventes à traiter (normal car DB vide)

---

## 🔎 Cause Probable

Le scraper utilise **Playwright** (navigateur headless) pour accéder au site gouvernemental.

Sur Render Free tier, Playwright nécessite des **dépendances système** qui ne sont probablement **pas installées**.

---

## 🧪 Test de Diagnostic

### 1. Attendez le redéploiement

Render est en train de déployer le nouveau code avec l'endpoint de diagnostic.
Attendez 2-3 minutes.

### 2. Testez le diagnostic

```bash
curl -s https://encheres-backend.onrender.com/api/v1/scheduler/diagnostic | python3 -m json.tool
```

**Ce que vous devriez voir :**

```json
{
  "system": { ... },
  "configuration": {
    "auction_base_url": "https://encheres-domaine.gouv.fr",
    ...
  },
  "database": {
    "sales_count": 0,
    "status": "connected"
  },
  "playwright": {
    "installed": true,
    "status": "installed_but_not_functional",
    "error": "Executable doesn't exist at ..."
  },
  "recommendations": [
    "Playwright is installed but cannot launch browser...",
    "Database has 0 sales. Run the discovery job first..."
  ]
}
```

---

## 🛠️ Solutions

### Solution 1 : Installer les Dépendances Playwright (Recommandé)

**Problème :** Render Free ne supporte pas bien Playwright car il nécessite des dépendances système lourdes.

**Options :**

#### A. Passer à un plan payant Render
- Le plan Starter ($7/mois) offre plus de ressources
- Meilleures chances que Playwright fonctionne

#### B. Ajouter les dépendances au Dockerfile

Modifiez `backend/Dockerfile` :

```dockerfile
FROM python:3.12-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \\
    wget \\
    libnss3 \\
    libnspr4 \\
    libdbus-1-3 \\
    libatk1.0-0 \\
    libatk-bridge2.0-0 \\
    libcups2 \\
    libdrm2 \\
    libxkbcommon0 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxfixes3 \\
    libxrandr2 \\
    libgbm1 \\
    libpango-1.0-0 \\
    libcairo2 \\
    libasound2 \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**⚠️ Attention :** Cela augmentera significativement la taille de l'image Docker et le temps de build.

---

### Solution 2 : Utiliser un Scraper plus Léger (Alternative)

Remplacer Playwright par des requêtes HTTP simples avec BeautifulSoup ou httpx.

**Avantages :**
- Pas de dépendances système
- Plus rapide
- Fonctionne sur Render Free

**Inconvénients :**
- Ne fonctionne pas si le site utilise JavaScript pour charger le contenu
- Peut être bloqué par des protections anti-bot

**Implémentation :**

Créez `backend/app/services/simple_scraper.py` :

```python
import httpx
from bs4 import BeautifulSoup
from typing import List
from app.services.sale_discovery import SaleSummary

class SimpleSaleDiscovery:
    """Scraper léger sans Playwright."""

    def __init__(self, base_url: str = "https://encheres-domaine.gouv.fr"):
        self.base_url = base_url

    async def fetch_sales(self) -> List[SaleSummary]:
        sales = []

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/ventes",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if response.status_code != 200:
                return sales

            soup = BeautifulSoup(response.text, "html.parser")

            # Adapter les sélecteurs selon la structure HTML réelle
            items = soup.select("div.fr-list-product__item")

            for item in items:
                # Parser chaque vente
                # ... (adaptation du code existant)
                pass

        return sales
```

---

### Solution 3 : Désactiver le Scraping Automatique (Temporaire)

Si le scraping n'est pas critique immédiatement :

1. Désactivez GitHub Actions temporairement
2. Ajoutez manuellement quelques ventes test en base
3. Testez le reste de l'application

**Ajout manuel de ventes test :**

```python
# Script à exécuter une fois
from app.models.sale import Sale
from app.db.session import AsyncSessionLocal

async def add_test_sales():
    async with AsyncSessionLocal() as db:
        sales = [
            Sale(
                sale_number=1001,
                title="Vente Test 1",
                description="Test",
                status="active",
                total_lots=10,
                url="https://encheres-domaine.gouv.fr/vente/1001"
            ),
            Sale(
                sale_number=1002,
                title="Vente Test 2",
                description="Test",
                status="upcoming",
                total_lots=5,
                url="https://encheres-domaine.gouv.fr/vente/1002"
            ),
        ]

        for sale in sales:
            db.add(sale)

        await db.commit()
```

---

### Solution 4 : Scraper Externe (Avancé)

Déployer le scraper séparément :

1. **GitHub Actions avec Playwright**
   - Exécuter le scraper dans GitHub Actions
   - Sauvegarder les résultats en JSON
   - Upload vers un endpoint API

2. **Service Séparé**
   - Déployer le scraper sur un autre service (Heroku, VPS, etc.)
   - Appeler l'API Render pour insérer les données

---

## 📊 Plan d'Action Recommandé

### Étape 1 : Diagnostic (Maintenant)

```bash
# Attendez 3 minutes que Render déploie

curl -s https://encheres-backend.onrender.com/api/v1/scheduler/diagnostic | python3 -m json.tool
```

Analysez l'output pour confirmer le problème Playwright.

### Étape 2 : Solution Court Terme

**Option A - Tester si Playwright fonctionne déjà :**

Parfois Playwright fonctionne malgré tout. Vérifiez les logs Render après l'exécution du diagnostic.

**Option B - Ajouter des ventes manuellement :**

Pour tester le reste de l'app pendant qu'on résout le scraping.

### Étape 3 : Solution Long Terme

**Choisir selon vos besoins :**

| Solution | Complexité | Coût | Fiabilité |
|----------|-----------|------|-----------|
| Installer deps Playwright | Moyenne | Temps de build ⬆️ | Moyenne |
| Scraper HTTP simple | Faible | Gratuit | Dépend du site |
| Plan payant Render | Faible | $7/mois | Haute |
| Scraper externe | Haute | Variable | Très haute |

**Ma recommandation :**
1. Essayez d'abord **Solution 2** (scraper HTTP simple)
2. Si ça ne marche pas, **Solution 1B** (deps Playwright)
3. En dernier recours, **Solution 4** (scraper externe dans GitHub Actions)

---

## 🔬 Vérifications Additionnelles

### Vérifier les Logs Render

1. Dashboard Render > Service backend > **Logs**
2. Recherchez des erreurs comme :
   - `"Executable doesn't exist"`
   - `"Failed to launch browser"`
   - `"No such file or directory"`

### Tester Localement

```bash
cd backend

# Installer Playwright
pip install playwright
playwright install chromium

# Tester le discovery
python3 -c "
import asyncio
from app.services.sale_discovery import SaleDiscoveryService

async def test():
    service = SaleDiscoveryService()
    sales = await service.fetch_sales(max_pages=1)
    print(f'Trouvé {len(sales)} ventes')
    for sale in sales[:3]:
        print(f'  - {sale.sale_number}: {sale.title}')

asyncio.run(test())
"
```

Si ça fonctionne localement mais pas sur Render → Problème de dépendances système.

---

## 📝 Résumé

**Problème identifié :** Playwright ne peut pas lancer le navigateur sur Render Free

**Solutions possibles :**
1. ✅ Installer dépendances système (Dockerfile)
2. ✅ Utiliser scraper HTTP simple (httpx + BeautifulSoup)
3. ✅ Upgrade plan Render
4. ✅ Scraper externe (GitHub Actions)

**Prochaine action :** Tester le diagnostic endpoint

```bash
curl https://encheres-backend.onrender.com/api/v1/scheduler/diagnostic
```

---

**Créé le :** 2025-10-20
**Mis à jour :** 2025-10-20 - RÉSOLU ✅

---

## ✅ SOLUTION FINALE (20/10/2025)

### Problème Réel

Le diagnostic a révélé que Playwright **fonctionnait correctement** sur Render Free. Le vrai problème était :

**Le site https://encheres-domaine.gouv.fr utilise un rendu JavaScript côté client (PWA/SPA)**

Playwright chargeait le HTML initial avant que JavaScript n'ait le temps de :
1. Faire les requêtes GraphQL vers l'API
2. Rendre le contenu dynamiquement dans le DOM

### Solution Implémentée

Ajout de `wait_for_selector()` dans 3 fichiers :

#### 1. `backend/app/services/sale_discovery.py` (ligne 177)
```python
await page.goto(url, wait_until="networkidle", timeout=30000)

# Wait for JavaScript to render content
try:
    await page.wait_for_selector(
        "div.fr-list-product__item, div.fr-card, article, div[class*='product'], div[class*='vente']",
        timeout=10000
    )
except Exception:
    import asyncio
    await asyncio.sleep(3)  # Fallback delay

html = await page.content()
```

#### 2. `backend/app/services/scraper.py` (ligne 77)
```python
await page.goto(url, wait_until="networkidle", timeout=30000)

# Wait for JavaScript to render content
try:
    await page.wait_for_selector(
        "ul.fr-list-product, div.fr-list-product__item, div.fr-card",
        timeout=10000
    )
except Exception:
    await asyncio.sleep(3)

html = await page.content()
```

#### 3. `backend/app/api/v1/endpoints/scheduler.py` (ligne 252)
Même fix dans l'endpoint de debug.

### Résultats

**Avant le fix :**
- Discovery job : 0 ventes trouvées
- Scraping job : 0 lots trouvés

**Après le fix :**
- ✅ Discovery job : **10 ventes créées**
- ✅ Scraping job : En cours de test

### Commits

- `9936fa0` - fix: Wait for JavaScript rendering in sale discovery scraper
- `da29937` - fix: Add JavaScript rendering wait to debug-scraper endpoint
- `40659c0` - fix: Add JavaScript rendering wait to lot scraping
- `28ca014` - feat: Add force-scrape-sale endpoint for testing

### Leçon Apprise

**Ne pas assumer que le problème vient de l'infrastructure** (Render Free, Playwright, dépendances).

Le diagnostic méthodique a montré que :
1. ✅ Playwright fonctionnait
2. ✅ La page se chargeait (659 KB HTML)
3. ❌ Les sélecteurs CSS ne trouvaient rien

→ **Le contenu était rendu dynamiquement par JavaScript**

La solution était donc simple : attendre que le JavaScript finisse de s'exécuter avant de parser le HTML.

---

**Statut :** ✅ RÉSOLU
**Temps de résolution :** ~2 heures (diagnostic + fix)
**Complexité réelle :** Faible (une fois le vrai problème identifié)
