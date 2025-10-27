# Enchères du Domaine - Microservices Architecture

Architecture microservices Node.js/TypeScript pour la plateforme Enchères du Domaine.

## Architecture

```
microservices/
├── api-gateway/           # Point d'entrée unique (port 3000)
├── auth-service/          # Authentification JWT (port 3001)
├── lots-service/          # Gestion des lots (port 3002)
├── sales-service/         # Gestion des ventes (port 3003)
├── scraper-service/       # Scraping web avec Puppeteer (port 3004)
├── notifications-service/ # Emails et notifications (port 3005)
├── shared/               # Code partagé (types, middleware, utils)
└── prisma/               # Schema unifié PostgreSQL
```

## Stack Technique

- **Runtime**: Node.js 20 + TypeScript
- **Framework**: Fastify (haute performance)
- **Base de données**: PostgreSQL avec Prisma ORM
- **Queue**: BullMQ + Redis (pour scraping async)
- **Auth**: JWT (jsonwebtoken)
- **Scraping**: Puppeteer
- **Email**: Nodemailer
- **Logs**: Pino
- **API Gateway**: Fastify HTTP Proxy

## Services

### API Gateway (port 3000)
- Point d'entrée unique pour toutes les requêtes
- Routing vers les microservices
- Rate limiting
- CORS configuré

### Auth Service (port 3001)
- POST `/api/v1/auth/register` - Inscription
- POST `/api/v1/auth/login` - Connexion
- POST `/api/v1/auth/logout` - Déconnexion
- GET `/api/v1/auth/me` - Profil utilisateur
- PATCH `/api/v1/auth/me` - Mise à jour profil

### Lots Service (port 3002)
- GET `/api/v1/lots` - Liste des lots (avec pagination et filtres)
- GET `/api/v1/lots/:id` - Détails d'un lot
- POST `/api/v1/lots` - Créer un lot (admin)
- PATCH `/api/v1/lots/:id` - Modifier un lot (admin)
- DELETE `/api/v1/lots/:id` - Supprimer un lot (admin)
- POST `/api/v1/lots/:id/favorite` - Ajouter aux favoris
- DELETE `/api/v1/lots/:id/favorite` - Retirer des favoris
- GET `/api/v1/lots/favorites/me` - Mes favoris
- POST `/api/v1/lots/alerts` - Créer une alerte
- GET `/api/v1/lots/alerts/me` - Mes alertes
- DELETE `/api/v1/lots/alerts/:id` - Supprimer une alerte

### Sales Service (port 3003)
- GET `/api/v1/sales` - Liste des ventes
- GET `/api/v1/sales/upcoming` - Ventes à venir
- GET `/api/v1/sales/:id` - Détails d'une vente
- POST `/api/v1/sales` - Créer une vente (admin)
- PATCH `/api/v1/sales/:id` - Modifier une vente (admin)
- DELETE `/api/v1/sales/:id` - Supprimer une vente (admin)

### Scraper Service (port 3004)
- POST `/api/v1/scraper/trigger` - Lancer un scraping (admin)
- GET `/api/v1/scraper/status/:jobId` - Status d'un job
- GET `/api/v1/scraper/jobs` - Liste des jobs récents

### Notifications Service (port 3005)
- GET `/api/v1/notifications/me` - Mes notifications
- POST `/api/v1/notifications/welcome` - Email de bienvenue (interne)
- POST `/api/v1/notifications/alert` - Email d'alerte (interne)

## Développement Local

### Prérequis
- Node.js 20+
- Docker et Docker Compose
- PostgreSQL 16
- Redis 7

### Installation

1. Installer les dépendances pour tous les services :

```bash
cd microservices

# Shared
cd shared && npm install && cd ..

# Services
cd auth-service && npm install && cd ..
cd lots-service && npm install && cd ..
cd sales-service && npm install && cd ..
cd scraper-service && npm install && cd ..
cd notifications-service && npm install && cd ..
cd api-gateway && npm install && cd ..
```

2. Créer le fichier `.env` :

```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

3. Lancer avec Docker Compose :

```bash
docker-compose up --build
```

Les services seront disponibles sur :
- API Gateway: http://localhost:3000
- Auth: http://localhost:3001
- Lots: http://localhost:3002
- Sales: http://localhost:3003
- Scraper: http://localhost:3004
- Notifications: http://localhost:3005

### Développement sans Docker

1. Lancer PostgreSQL et Redis localement

2. Générer les clients Prisma :

```bash
cd auth-service && npx prisma generate && npx prisma db push && cd ..
cd lots-service && npx prisma generate && npx prisma db push && cd ..
cd sales-service && npx prisma generate && npx prisma db push && cd ..
cd notifications-service && npx prisma generate && npx prisma db push && cd ..
```

3. Lancer chaque service en mode dev :

```bash
# Terminal 1
cd auth-service && npm run dev

# Terminal 2
cd lots-service && npm run dev

# Terminal 3
cd sales-service && npm run dev

# Terminal 4
cd scraper-service && npm run dev

# Terminal 5
cd notifications-service && npm run dev

# Terminal 6
cd api-gateway && npm run dev
```

## Déploiement sur Render

Le fichier `render.yaml` configure tous les services pour le déploiement automatique.

### Prérequis Render
1. Compte Render.com
2. Repository Git connecté
3. Variables d'environnement configurées

### Déploiement

```bash
git add .
git commit -m "feat: Add microservices architecture"
git push origin master
```

Render détectera automatiquement `render.yaml` et déploiera tous les services.

### Services Render
- API Gateway: Point d'entrée principal
- PostgreSQL: Base de données partagée
- Redis: Queue pour le scraping
- 5 Web Services (auth, lots, sales, scraper, notifications)

## Monitoring

Utilisez les endpoints `/health` de chaque service pour le monitoring :

```bash
curl http://localhost:3000/health  # API Gateway
curl http://localhost:3001/health  # Auth
curl http://localhost:3002/health  # Lots
curl http://localhost:3003/health  # Sales
curl http://localhost:3004/health  # Scraper
curl http://localhost:3005/health  # Notifications
```

## Tests

Créer un utilisateur et tester l'API :

```bash
# Register
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Get lots
curl http://localhost:3000/api/v1/lots

# Get sales
curl http://localhost:3000/api/v1/sales
```

## Performance

- **Fastify**: 3x plus rapide qu'Express
- **Prisma**: Queries optimisées avec pooling
- **BullMQ**: Queue async pour scraping
- **Redis**: Cache et queue ultra-rapide
- **Puppeteer**: Scraping concurrent

## Sécurité

- JWT avec expiration (7 jours)
- Bcrypt pour les mots de passe
- Rate limiting (100 req/min)
- CORS configuré
- Variables d'environnement sécurisées
- Validation des entrées

## Licence

MIT
