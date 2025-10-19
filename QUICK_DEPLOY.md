# ⚡ Déploiement Rapide - v2.0.0

Guide express pour déployer en 10 minutes.

---

## 🚀 Déploiement Local (Développement)

```bash
# 1. Cloner le projet
git clone https://github.com/votre-username/Projet_encheres.git
cd Projet_encheres

# 2. Copier et configurer .env
cp .env.example .env
# Éditer .env avec vos valeurs (au minimum SECRET_KEY et POSTGRES_PASSWORD)

# 3. Démarrer avec Docker
docker compose up -d

# 4. Exécuter les migrations
docker compose exec backend alembic upgrade head

# 5. Accéder à l'application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**C'est tout!** L'application est accessible.

---

## 🌐 Déploiement Production (Serveur)

### Prérequis
- Serveur Ubuntu 22.04 avec Docker installé
- Nom de domaine configuré (DNS pointant vers votre serveur)

### Commandes

```bash
# 1. Sur votre serveur
ssh user@your-server

# 2. Installer Docker (si pas déjà fait)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Se déconnecter et se reconnecter

# 3. Cloner le projet
cd /opt && sudo mkdir encheres && sudo chown $USER:$USER encheres
cd encheres
git clone https://github.com/votre-username/Projet_encheres.git .

# 4. Configurer .env PRODUCTION
cp .env.example .env
nano .env

# ⚠️  MODIFIER CES VALEURS:
# SECRET_KEY=<générer avec: python3 -c "import secrets; print(secrets.token_urlsafe(32))">
# POSTGRES_PASSWORD=<mot de passe fort>
# DEBUG=false
# BACKEND_CORS_ORIGINS=https://yourdomain.com
# VITE_API_URL=https://yourdomain.com/api/v1

# 5. Démarrer en production
docker compose -f docker-compose.prod.yml up -d

# 6. Migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 7. Installer Nginx + SSL (Let's Encrypt)
sudo apt install nginx certbot python3-certbot-nginx -y

# 8. Configurer Nginx (voir DEPLOYMENT.md section 4.2)
sudo nano /etc/nginx/sites-available/encheres
sudo ln -s /etc/nginx/sites-available/encheres /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 9. Obtenir certificat SSL
sudo certbot --nginx -d yourdomain.com

# 10. Ouvrir les ports firewall
sudo ufw allow 22  # SSH
sudo ufw allow 80  # HTTP
sudo ufw allow 443 # HTTPS
sudo ufw enable
```

**✅ C'est déployé!** Accédez à https://yourdomain.com

---

## 🔍 Vérifications Rapides

```bash
# Tous les conteneurs en état "Up"?
docker compose -f docker-compose.prod.yml ps

# Logs (si problème)
docker compose -f docker-compose.prod.yml logs -f

# Backend accessible?
curl http://localhost:8000/health

# Frontend accessible?
curl http://localhost:80
```

---

## 📦 Mise à Jour Rapide

```bash
cd /opt/encheres
git pull origin master
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 🚨 Problème?

1. **Conteneurs ne démarrent pas**: `docker compose -f docker-compose.prod.yml logs`
2. **Base de données erreur**: Vérifier `.env` (POSTGRES_PASSWORD correct?)
3. **Frontend 404**: Attendre 1-2 min (build initial)
4. **CORS error**: Vérifier `BACKEND_CORS_ORIGINS` dans `.env`

**Documentation complète**: Voir `DEPLOYMENT.md`

---

**Version**: 2.0.0
