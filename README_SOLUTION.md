# 🎯 SOLUTION COMPLÈTE - Erreur Tables Manquantes

## 🔍 Problème Final Identifié

L'erreur était causée par **deux problèmes** :

1. ❌ Les tables n'existaient pas dans la base de données
2. ❌ L'extension PostgreSQL `pg_trgm` n'était pas installée

**Erreur détectée :**
```
asyncpg.exceptions.UndefinedObjectError: operator class "gin_trgm_ops" does not exist for access method "gin"
```

Cette extension est nécessaire pour les index de recherche full-text sur les lots.

## ✅ SOLUTION EN UNE COMMANDE

Exécutez simplement :

```bash
sudo ./setup_database.sh
```

Ce script va automatiquement :
1. ✅ Installer l'extension `pg_trgm` dans PostgreSQL
2. ✅ Créer toutes les tables de la base de données
3. ✅ Vérifier que tout est correctement installé

## 📋 Solution Étape par Étape

### Méthode 1 : Script Automatique (Recommandé)

```bash
# Rendre le script exécutable
chmod +x setup_database.sh

# Exécuter le script
sudo ./setup_database.sh
```

### Méthode 2 : Commandes Manuelles

Si vous préférez exécuter les commandes une par une :

```bash
# 1. Installer l'extension pg_trgm
sudo docker exec encheres_db psql -U postgres -d encheres \
  -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# 2. Créer les tables
sudo docker exec encheres_backend python3 /app/init_db.py

# 3. Vérifier les tables
sudo docker exec encheres_db psql -U postgres -d encheres \
  -c "\dt"
```

## 🧪 Vérification

### Test 1 : Vérifier les tables créées

```bash
sudo docker exec encheres_db psql -U postgres -d encheres -c "\dt"
```

Vous devriez voir :
```
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alerts          | table | postgres
 public | comments        | table | postgres
 public | favorites       | table | postgres
 public | lots            | table | postgres
 public | notifications   | table | postgres
 public | price_history   | table | postgres
 public | sales           | table | postgres
 public | users           | table | postgres
```

### Test 2 : Tester l'inscription

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Réponse attendue (code 201) :**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "is_active": true,
  "is_admin": false,
  "role": "user",
  ...
}
```

### Test 3 : Test complet avec le script

```bash
python3 test_api.py
```

**Résultat attendu :**
```
✓ Health Check........................... PASSÉ
✓ Inscription............................ PASSÉ
✓ Connexion.............................. PASSÉ
✓ Info utilisateur....................... PASSÉ
✓ Récupération des lots.................. PASSÉ
✓ Récupération des ventes................ PASSÉ

Résultat final: 6/6 tests réussis
🎉 Tous les tests sont passés avec succès!
```

## 🚀 Utilisation de l'Application

### 1. Créer un compte utilisateur

**Via le frontend :**
- Ouvrez http://localhost:5173
- Cliquez sur "S'inscrire"
- Remplissez le formulaire

**Via l'API :**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "votre@email.com",
    "username": "votreusername",
    "password": "votrepassword",
    "full_name": "Votre Nom"
  }'
```

### 2. Rendre un utilisateur admin (pour le scraping)

```bash
sudo docker exec encheres_db psql -U postgres -d encheres \
  -c "UPDATE users SET is_admin = true, role = 'admin' WHERE email = 'votre@email.com';"
```

### 3. Se connecter et récupérer le token

**Via l'API :**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=votre@email.com&password=votrepassword"
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

Copiez le `access_token` pour l'utiliser dans les requêtes suivantes.

### 4. Lancer le scraping

```bash
# Définir le token
TOKEN="votre_access_token_ici"

# Scraper la vente #42
curl -X POST "http://localhost:8000/api/v1/admin/scrape?sale_number=42" \
  -H "Authorization: Bearer $TOKEN"

# Scraper plusieurs ventes
curl -X POST "http://localhost:8000/api/v1/admin/scrape-multiple" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sale_numbers": [42, 43, 44, 45]}'
```

### 5. Consulter les lots

```bash
# Via l'API
curl http://localhost:8000/api/v1/lots?page=1&size=10

# Via le frontend
# Ouvrez http://localhost:5173
```

## 🛠️ Commandes Utiles

### Gestion des conteneurs

```bash
# Voir l'état
sudo docker ps

# Redémarrer le backend
sudo docker restart encheres_backend

# Redémarrer tout
sudo docker-compose restart

# Voir les logs
sudo docker logs encheres_backend --tail 50
sudo docker logs encheres_backend -f  # En temps réel
```

### Base de données

```bash
# Se connecter à PostgreSQL
sudo docker exec -it encheres_db psql -U postgres -d encheres

# Commandes utiles dans psql:
\dt                          # Lister les tables
\d users                     # Décrire la table users
\dx                          # Lister les extensions
SELECT * FROM users;         # Voir les utilisateurs
SELECT COUNT(*) FROM lots;   # Compter les lots
\q                           # Quitter
```

### Réinitialisation complète (si nécessaire)

⚠️ **Attention : Cela supprime toutes les données !**

```bash
# Arrêter les conteneurs
sudo docker-compose down

# Supprimer le volume de la base de données
sudo docker volume rm projet_encheres_postgres_data

# Redémarrer
sudo docker-compose up -d

# Attendre que tout démarre
sleep 10

# Reconfigurer la base de données
sudo ./setup_database.sh
```

## 📊 Architecture de la Base de Données

### Tables créées

| Table | Description |
|-------|-------------|
| **users** | Utilisateurs de l'application |
| **lots** | Lots aux enchères scrapés |
| **sales** | Ventes (groupes de lots) |
| **favorites** | Lots favoris des utilisateurs |
| **alerts** | Alertes de prix/nouveaux lots |
| **notifications** | Notifications pour les utilisateurs |
| **price_history** | Historique des changements de prix |
| **comments** | Commentaires sur les lots |

### Relations

- Un **utilisateur** peut avoir plusieurs favoris, alertes et notifications
- Une **vente** contient plusieurs **lots**
- Un **lot** peut avoir plusieurs entrées dans **price_history**
- Les **favoris** lient un utilisateur à un lot

## 🐛 Résolution de Problèmes

### Erreur : "relation does not exist"

```bash
# Recréer les tables
sudo ./setup_database.sh
```

### Erreur : "gin_trgm_ops does not exist"

```bash
# Installer l'extension
sudo docker exec encheres_db psql -U postgres -d encheres \
  -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# Puis recréer les tables
sudo docker exec encheres_backend python3 /app/init_db.py
```

### Le backend ne démarre pas

```bash
# Vérifier les logs
sudo docker logs encheres_backend --tail 100

# Redémarrer
sudo docker restart encheres_backend
```

### Les tests échouent

```bash
# Vérifier que la base de données est accessible
nc -zv localhost 5432

# Vérifier que le backend répond
curl http://localhost:8000/health

# Vérifier les tables
sudo docker exec encheres_db psql -U postgres -d encheres -c "\dt"
```

## 📖 Documentation API

L'API Swagger est disponible à : **http://localhost:8000/docs**

Vous y trouverez :
- 📝 Documentation complète de tous les endpoints
- 🧪 Interface de test interactive
- 📋 Schémas des modèles de données

## ✅ Checklist Finale

Avant de commencer à utiliser l'application, vérifiez :

- [ ] ✅ Les conteneurs sont démarrés : `sudo docker ps`
- [ ] ✅ L'extension pg_trgm est installée
- [ ] ✅ Les tables sont créées
- [ ] ✅ Le backend répond : `curl http://localhost:8000/health`
- [ ] ✅ Vous pouvez vous inscrire
- [ ] ✅ Vous pouvez vous connecter
- [ ] ✅ Le frontend est accessible : http://localhost:5173

## 🎉 Félicitations !

Si toutes les vérifications passent, votre application est **100% opérationnelle** !

Vous pouvez maintenant :
- 👥 Créer des comptes utilisateurs
- 🔍 Consulter les lots
- ⭐ Ajouter des favoris
- 🔔 Configurer des alertes
- 🛠️ (Admin) Scraper de nouvelles ventes

**Bon enchères ! 🎯**
