# 🚀 Render.com - Guide Pas à Pas (Méthode Manuelle)

Si le Blueprint automatique pose problème, suivez ce guide manuel.

---

## 📋 Prérequis

- ✅ Code sur GitHub
- ✅ Compte Render.com créé et lié à GitHub

---

## Étape 1 : Créer la Base de Données PostgreSQL

1. **Dashboard Render** → Cliquer **"New +"**
2. Sélectionner **"PostgreSQL"**
3. Configurer :
   ```
   Name: encheres-db
   Database: encheres
   User: encheres_user
   Region: Frankfurt (EU Central)
   Plan: Free
   ```
4. Cliquer **"Create Database"**
5. **IMPORTANT** : Une fois créée, aller dans l'onglet **"Info"**
6. **COPIER** l'**"Internal Database URL"** (commence par `postgresql://...`)
   - Format : `postgresql://encheres_user:PASSWORD@dpg-xxxxx/encheres`
   - ⚠️ Gardez-le dans un fichier texte temporaire

---

## Étape 2 : Créer le Backend API

1. **Dashboard** → **"New +"** → **"Web Service"**
2. Cliquer **"Build and deploy from a Git repository"**
3. **Connect** votre repo **"Projet_encheres"**
4. Configurer :

   ```
   Name: encheres-backend
   Region: Frankfurt (EU Central)
   Branch: master (ou main)
   Root Directory: (laisser vide)
   Environment: Docker
   Dockerfile Path: ./backend/Dockerfile
   Docker Build Context Directory: ./backend
   ```

5. **Instance Type** : Sélectionner **"Free"**

6. **Advanced** → **Environment Variables** → Ajouter :

   ```
   DATABASE_URL = <coller votre Internal Database URL>

   DATABASE_URL_SYNC = <même URL mais remplacer postgresql+asyncpg par postgresql>

   SECRET_KEY = <générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))">

   DEBUG = false

   BACKEND_CORS_ORIGINS = https://encheres-frontend.onrender.com

   ALGORITHM = HS256

   ACCESS_TOKEN_EXPIRE_MINUTES = 30

   REFRESH_TOKEN_EXPIRE_DAYS = 7

   RATE_LIMIT_PER_MINUTE = 60

   AUTH_RATE_LIMIT_PER_MINUTE = 5

   DB_POOL_SIZE = 10

   DB_MAX_OVERFLOW = 5

   DB_POOL_RECYCLE = 3600
   ```

7. **Health Check Path** : `/health`

8. Cliquer **"Create Web Service"**

**⏱️ Attendre 5-10 minutes** que le backend se déploie. Vous verrez les logs en temps réel.

---

## Étape 3 : Créer le Frontend

1. **Dashboard** → **"New +"** → **"Static Site"**
2. **Connect** votre repo **"Projet_encheres"** (si pas déjà fait)
3. Configurer :

   ```
   Name: encheres-frontend
   Branch: master (ou main)
   Root Directory: (laisser vide)
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/dist
   ```

4. **Environment Variables** :

   ```
   VITE_API_URL = https://encheres-backend.onrender.com/api/v1
   ```

   ⚠️ **IMPORTANT** : Remplacez `encheres-backend` par le vrai nom de votre service backend si différent.

5. Cliquer **"Create Static Site"**

**⏱️ Attendre 3-5 minutes** pour le build.

---

## Étape 4 : Mettre à Jour le CORS

Une fois le **frontend déployé**, vous aurez son URL (ex: `https://encheres-frontend.onrender.com`).

**Retourner dans le Backend :**

1. Aller dans **"encheres-backend"** → **"Environment"**
2. Modifier `BACKEND_CORS_ORIGINS` :
   ```
   BACKEND_CORS_ORIGINS = https://encheres-frontend.onrender.com
   ```
3. **Save Changes**
4. Le backend va redéployer automatiquement (~2 minutes)

---

## Étape 5 : Exécuter les Migrations (Optionnel)

Si les migrations ne se sont pas exécutées automatiquement :

1. Aller dans **"encheres-backend"**
2. Cliquer sur **"Shell"** (à gauche)
3. Exécuter :
   ```bash
   alembic upgrade head
   ```

---

## ✅ Vérification

### Backend
- URL : `https://encheres-backend.onrender.com`
- API Docs : `https://encheres-backend.onrender.com/docs`
- Health : `https://encheres-backend.onrender.com/health`

**Tester dans le navigateur :**
```
https://encheres-backend.onrender.com/health
```

Devrait retourner : `{"status": "healthy"}`

### Frontend
- URL : `https://encheres-frontend.onrender.com`

**Ouvrir dans le navigateur et vérifier que :**
- La page se charge
- Vous pouvez créer un compte
- Vous pouvez vous connecter

---

## 🚨 Dépannage

### Erreur : "Application failed to respond"

**Solution :**
1. Vérifier les logs du backend
2. Vérifier que `DATABASE_URL` est correcte
3. Vérifier que les migrations ont été exécutées

### Erreur : CORS Policy

**Solution :**
1. Vérifier que `BACKEND_CORS_ORIGINS` contient l'URL exacte du frontend
2. Pas d'espace, pas de `/` à la fin
3. Format : `https://encheres-frontend.onrender.com` (sans slash final)

### Backend ne démarre pas

**Vérifier dans les logs :**
- "Dockerfile not found" → Vérifier le `Dockerfile Path`
- "Database connection failed" → Vérifier `DATABASE_URL`
- "SECRET_KEY too short" → Générer une nouvelle clé de 32+ caractères

### Frontend : Page blanche

**Solution :**
1. Vérifier les logs du build
2. Vérifier que `Publish Directory` = `frontend/dist`
3. Vérifier que `VITE_API_URL` pointe vers le bon backend

---

## 📊 Récapitulatif des URLs

Une fois déployé, vous aurez :

```
Database:  dpg-xxxxx.frankfurt-postgres.render.com (interne)
Backend:   https://encheres-backend.onrender.com
API Docs:  https://encheres-backend.onrender.com/docs
Frontend:  https://encheres-frontend.onrender.com
```

---

## 🎉 Terminé !

Votre application est maintenant **EN LIGNE** et accessible publiquement avec **HTTPS** !

**Prochaines étapes :**
- Tester toutes les fonctionnalités
- Partager l'URL avec vos utilisateurs
- Configurer un domaine personnalisé (optionnel)

---

**Version** : 2.0.0
**Support** : Voir DEPLOYMENT.md et FREE_HOSTING.md
