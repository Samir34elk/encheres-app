# 🚀 Guide de Déploiement - Enchères du Domaine v2.0.0

Ce guide vous accompagne pas à pas pour déployer l'application en production de manière sécurisée.

---

## 📋 Prérequis

### Serveur de Production
- **OS**: Ubuntu 22.04 LTS (recommandé) ou Debian 11+
- **RAM**: Minimum 2 GB (4 GB recommandé)
- **CPU**: 2 cores minimum
- **Stockage**: 20 GB minimum
- **Accès**: SSH avec clés publiques/privées

### Logiciels Requis
- Docker 24.0+
- Docker Compose 2.0+
- Git
- Nginx (comme reverse proxy) ou Caddy
- Certificat SSL/TLS (Let's Encrypt recommandé)

---

## 🔐 Étape 1 : Préparation Sécurité

### 1.1 Générer une SECRET_KEY Sécurisée

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copiez la clé générée, vous en aurez besoin pour `.env`.

### 1.2 Créer un Mot de Passe PostgreSQL Fort

```bash
openssl rand -base64 32
```

---

## 📦 Étape 2 : Préparation du Serveur

### 2.1 Connexion au Serveur

```bash
ssh user@your-server-ip
```

### 2.2 Mise à Jour du Système

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Installation de Docker

```bash
# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Se reconnecter pour appliquer les changements
exit
ssh user@your-server-ip
```

### 2.4 Installation de Docker Compose

```bash
sudo apt install docker-compose-plugin -y
```

### 2.5 Configuration du Firewall

```bash
# Installer ufw (si pas déjà installé)
sudo apt install ufw -y

# Configurer les règles
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS

# Activer le firewall
sudo ufw enable
```

---

## 📂 Étape 3 : Déploiement de l'Application

### 3.1 Cloner le Projet

```bash
cd /opt
sudo mkdir -p encheres
sudo chown $USER:$USER encheres
cd encheres

git clone https://github.com/votre-username/Projet_encheres.git .
```

### 3.2 Configurer les Variables d'Environnement

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

**Modifiez ces valeurs OBLIGATOIREMENT:**

```env
# SÉCURITÉ - CRITIQUE
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_FROM_STEP_1.1
POSTGRES_PASSWORD=YOUR_GENERATED_PASSWORD_FROM_STEP_1.2

# DEBUG - DOIT ÊTRE false
DEBUG=false

# CORS - Votre domaine
BACKEND_CORS_ORIGINS=https://encheres.yourdomain.com

# URLs
VITE_API_URL=https://encheres.yourdomain.com/api/v1
```

### 3.3 Construire les Images Docker

```bash
docker compose -f docker-compose.prod.yml build
```

### 3.4 Démarrer les Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 3.5 Vérifier que les Conteneurs Fonctionnent

```bash
docker compose -f docker-compose.prod.yml ps
```

Vous devriez voir 4 conteneurs en état "Up":
- encheres_db_prod
- encheres_redis_prod
- encheres_backend_prod
- encheres_frontend_prod

### 3.6 Exécuter les Migrations de Base de Données

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 3.7 Créer un Utilisateur Admin (Optionnel)

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin
```

---

## 🌐 Étape 4 : Configuration du Reverse Proxy (Nginx)

### 4.1 Installer Nginx

```bash
sudo apt install nginx -y
```

### 4.2 Créer la Configuration du Site

```bash
sudo nano /etc/nginx/sites-available/encheres
```

**Contenu:**

```nginx
server {
    listen 80;
    server_name encheres.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name encheres.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/encheres.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/encheres.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Max upload size
    client_max_body_size 10M;
}
```

### 4.3 Activer le Site

```bash
sudo ln -s /etc/nginx/sites-available/encheres /etc/nginx/sites-enabled/
sudo nginx -t  # Tester la configuration
sudo systemctl restart nginx
```

---

## 🔒 Étape 5 : Installer le Certificat SSL (Let's Encrypt)

### 5.1 Installer Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 5.2 Obtenir le Certificat

```bash
sudo certbot --nginx -d encheres.yourdomain.com
```

Suivez les instructions à l'écran.

### 5.3 Renouvellement Automatique

```bash
# Tester le renouvellement
sudo certbot renew --dry-run

# Le renouvellement automatique est déjà configuré via systemd timer
sudo systemctl status certbot.timer
```

---

## 📊 Étape 6 : Monitoring et Maintenance

### 6.1 Vérifier les Logs

```bash
# Logs de tous les conteneurs
docker compose -f docker-compose.prod.yml logs -f

# Logs backend uniquement
docker compose -f docker-compose.prod.yml logs -f backend

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
```

### 6.2 Sauvegardes de la Base de Données

**Script de Backup Automatique:**

```bash
sudo nano /opt/scripts/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="encheres_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

docker compose -f /opt/encheres/docker-compose.prod.yml exec -T db pg_dump -U postgres encheres > "$BACKUP_DIR/$FILENAME"

# Compresser
gzip "$BACKUP_DIR/$FILENAME"

# Garder uniquement les 30 derniers jours
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup créé: $FILENAME.gz"
```

```bash
chmod +x /opt/scripts/backup-db.sh

# Ajouter à crontab (tous les jours à 2h du matin)
sudo crontab -e
# Ajouter: 0 2 * * * /opt/scripts/backup-db.sh >> /var/log/db-backup.log 2>&1
```

### 6.3 Mise à Jour de l'Application

```bash
cd /opt/encheres

# Sauvegarder d'abord
/opt/scripts/backup-db.sh

# Pull les nouvelles modifications
git pull origin master

# Rebuild les images
docker compose -f docker-compose.prod.yml build

# Redémarrer avec downtime minimal
docker compose -f docker-compose.prod.yml up -d

# Exécuter les migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

---

## 🔍 Étape 7 : Vérification Post-Déploiement

### 7.1 Checklist de Sécurité

```bash
# ✅ Vérifier que DEBUG=false
docker compose -f docker-compose.prod.yml exec backend python -c "from app.core.config import settings; print(f'DEBUG: {settings.DEBUG}')"

# ✅ Vérifier la SECRET_KEY (doit être longue et aléatoire)
docker compose -f docker-compose.prod.yml exec backend python -c "from app.core.config import settings; print(f'SECRET_KEY length: {len(settings.SECRET_KEY)}')"

# ✅ Vérifier le CORS
docker compose -f docker-compose.prod.yml exec backend python -c "from app.core.config import settings; print(f'CORS: {settings.BACKEND_CORS_ORIGINS}')"

# ✅ Tester HTTPS
curl -I https://encheres.yourdomain.com

# ✅ Vérifier les headers de sécurité
curl -I https://encheres.yourdomain.com | grep -E "(Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options)"
```

### 7.2 Tests Fonctionnels

1. **Frontend**: Ouvrir https://encheres.yourdomain.com
2. **Inscription**: Créer un compte utilisateur
3. **Login**: Se connecter
4. **API**: Tester https://encheres.yourdomain.com/api/v1/docs

### 7.3 Monitoring

```bash
# CPU/RAM usage
docker stats

# Disk usage
df -h

# Network
sudo netstat -tuln | grep -E '(80|443|8000|5432|6379)'
```

---

## 🚨 Dépannage

### Problème: Les conteneurs ne démarrent pas

```bash
# Vérifier les logs
docker compose -f docker-compose.prod.yml logs

# Redémarrer proprement
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Problème: Base de données inaccessible

```bash
# Vérifier la santé du conteneur
docker compose -f docker-compose.prod.yml exec db pg_isready -U postgres

# Se connecter à la DB
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d encheres
```

### Problème: Certificat SSL expiré

```bash
# Renouveler manuellement
sudo certbot renew

# Redémarrer Nginx
sudo systemctl restart nginx
```

---

## 📞 Support

- **Documentation**: Voir `SECURITY.md`, `TESTING.md`
- **Issues**: https://github.com/votre-username/Projet_encheres/issues
- **Email**: support@encheres.com

---

## 🎉 Félicitations!

Votre application est maintenant déployée en production de manière sécurisée!

**Prochaines étapes recommandées:**
- Configurer un monitoring (Grafana, Prometheus)
- Mettre en place des alertes (Sentry)
- Configurer des backups automatiques hors site
- Activer le logging centralisé (ELK Stack, Loki)
- Tests de charge (Apache JMeter, Locust)

---

**Version**: 2.0.0
**Date**: 2025-10-20
**Auteur**: Expert DevOps & Sécurité
