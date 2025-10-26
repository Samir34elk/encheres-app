# 🚀 Démarrage Rapide - Architecture Microservices

## 📖 Par où commencer ?

Lisez les documents dans cet ordre :

1. **[README_MICROSERVICES.md](README_MICROSERVICES.md)** ← **COMMENCER ICI**
   - Vue d'ensemble du projet
   - Architecture complète
   - Commandes de démarrage
   - Guide rapide

2. **[MICROSERVICES_SUMMARY.md](MICROSERVICES_SUMMARY.md)**
   - Résumé exécutif complet
   - Comparaison avant/après
   - Détails techniques
   - Configuration

3. **[MICROSERVICES_DEPLOYMENT.md](MICROSERVICES_DEPLOYMENT.md)**
   - Guide de déploiement pas à pas
   - Configuration détaillée
   - Monitoring et maintenance
   - Troubleshooting

4. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)**
   - Migration depuis le monolithe
   - Mapping des services
   - Tests post-migration

5. **[services/README.md](services/README.md)**
   - Architecture technique détaillée
   - Communication inter-services
   - Développement

6. **[TRAVAIL_REALISE.md](TRAVAIL_REALISE.md)**
   - Résumé de tout le travail effectué
   - Statistiques et métriques

---

## ⚡ Démarrage Ultra-Rapide

```bash
# 1. Démarrer tous les microservices
./start-microservices.sh

# 2. Vérifier que tout fonctionne
curl http://localhost:8000/health
curl http://localhost:8003/health

# 3. Accéder à l'application
# - Frontend: http://localhost:5173
# - API: http://localhost:8000
# - RabbitMQ UI: http://localhost:15672 (guest/guest)
```

---

## 🎯 Ce qui a été fait

✅ **6 microservices** créés et fonctionnels
✅ **GitHub Actions remplacé** par le Scraper Service (port 8003)
✅ **API Gateway** pour le routage centralisé (port 8000)
✅ **Message Bus** RabbitMQ pour communication asynchrone
✅ **Documentation complète** (7700+ lignes)
✅ **Scripts d'automatisation** pour le déploiement

---

## 📦 Services Déployés

| Service | Port | Rôle |
|---------|------|------|
| **API Gateway** | 8000 | Point d'entrée unique |
| **Auth Service** | 8001 | Authentification |
| **Core Service** | 8002 | Ventes, lots, favoris |
| **Scraper Service** | 8003 | **Remplace GitHub Actions** ⚡ |
| **Notification Service** | 8004 | Emails, notifications |
| **Admin Service** | 8005 | Administration |

---

## 🔥 Point Clé: Scraper Service

Le **Scraper Service** (port 8003) remplace **complètement** les workflows GitHub Actions.

### Jobs Automatiques

1. **Scraping des ventes** - Toutes les 15 minutes
   - Remplace: `GitHub Actions cron: '*/15 * * * *'`

2. **Découverte des ventes** - Tous les jours à 3h
   - Remplace: `GitHub Actions cron: '0 3 * * *'`

3. **Mise à jour des prix** - Toutes les minutes
   - Remplace: `GitHub Actions cron: '* * * * *'`

### Contrôle

```bash
# Status
curl http://localhost:8003/health

# Liste des jobs
curl http://localhost:8003/api/v1/scraper/jobs

# Déclencher manuellement
curl -X POST http://localhost:8003/api/v1/scraper/trigger/scrape_sales

# Logs en temps réel
docker-compose -f docker-compose.microservices.yml logs -f scraper-service
```

---

## 📚 Structure du Projet

```
.
├── START_HERE.md                     ← VOUS ÊTES ICI
├── README_MICROSERVICES.md           ← Lire en premier
├── MICROSERVICES_SUMMARY.md          ← Résumé complet
├── MICROSERVICES_DEPLOYMENT.md       ← Guide déploiement
├── MIGRATION_GUIDE.md                ← Guide migration
├── TRAVAIL_REALISE.md                ← Résumé du travail
│
├── start-microservices.sh            ← Script de démarrage
├── docker-compose.microservices.yml  ← Orchestration
│
├── services/                         ← Microservices
│   ├── shared/                       ← Bibliothèque commune
│   ├── auth-service/                 ← Port 8001
│   ├── core-service/                 ← Port 8002
│   ├── scraper-service/              ← Port 8003 (remplace GitHub Actions)
│   ├── notification-service/         ← Port 8004
│   ├── admin-service/                ← Port 8005
│   ├── api-gateway/                  ← NGINX
│   └── README.md
│
├── scripts/
│   └── generate_microservices.py     ← Génération auto
│
├── backend/                          ← Ancien monolithe (archivé)
└── frontend/                         ← Frontend (inchangé)
```

---

## 🛠️ Commandes Essentielles

```bash
# Démarrer tout
./start-microservices.sh

# Voir les logs
docker-compose -f docker-compose.microservices.yml logs -f

# Arrêter tout
docker-compose -f docker-compose.microservices.yml down

# Redémarrer un service
docker-compose -f docker-compose.microservices.yml restart scraper-service

# Status des conteneurs
docker-compose -f docker-compose.microservices.yml ps
```

---

## ✅ Checklist

- [ ] Lire README_MICROSERVICES.md
- [ ] Démarrer avec ./start-microservices.sh
- [ ] Vérifier que tous les services sont "healthy"
- [ ] Tester l'authentification
- [ ] Vérifier que le Scraper Service scheduler est actif
- [ ] Accéder au frontend (http://localhost:5173)
- [ ] Consulter RabbitMQ UI (http://localhost:15672)

---

## 🆘 Besoin d'Aide ?

1. **Documentation** : Lire README_MICROSERVICES.md
2. **Problèmes** : Consulter MICROSERVICES_DEPLOYMENT.md (section Troubleshooting)
3. **Logs** : `docker-compose -f docker-compose.microservices.yml logs -f`
4. **Health checks** : `curl http://localhost:PORT/health`

---

## 🎉 Félicitations !

Vous utilisez maintenant une **architecture microservices moderne** sans dépendance à GitHub Actions !

**Prêt pour la production** 🚀
