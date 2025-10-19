# Guide de Résolution des Problèmes

## Résumé des modifications effectuées

### 1. Amélioration du Scraper (`backend/app/services/scraper.py`)

**Changements:**
- Ajout du support pour scraper différents numéros de vente
- Création automatique des ventes (modèle `Sale`) avant le scraping
- Association des lots à leur vente via `sale_id`
- Mise à jour des métadonnées de vente (total_lots, is_scraped, last_scraped_at)

**Nouvelles méthodes:**
- `__init__(db, sale_number=None)` : Le numéro de vente est maintenant optionnel
- `ensure_sale_exists()` : Crée ou récupère l'enregistrement de la vente

### 2. Nouveaux Endpoints Admin (`backend/app/api/v1/endpoints/admin.py`)

**Endpoints créés:**

#### POST `/api/v1/admin/scrape`
Déclenche le scraping d'une vente spécifique ou de la vente par défaut.

**Paramètres:**
- `sale_number` (optionnel) : Numéro de la vente à scraper

**Exemple:**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/scrape?sale_number=45" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### POST `/api/v1/admin/scrape-multiple`
Déclenche le scraping de plusieurs ventes en une seule requête.

**Body JSON:**
```json
{
  "sale_numbers": [42, 43, 44, 45]
}
```

**Exemple:**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/scrape-multiple" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sale_numbers": [42, 43, 44, 45]}'
```

## Problème actuel : Erreurs 500

Les tests ont révélé des erreurs 500 (Internal Server Error) lors de :
- L'inscription
- La connexion
- La récupération des lots
- La récupération des ventes

### Causes possibles

1. **Problème de permissions Docker**
   - Votre utilisateur n'est pas dans le groupe `docker`
   - Solution: `sudo usermod -aG docker $USER && newgrp docker`

2. **Problème de base de données**
   - Les tables ne sont peut-être pas créées
   - Les migrations ne sont peut-être pas exécutées

3. **Erreur au démarrage du backend**
   - Une exception Python qui bloque les requêtes

## Actions à effectuer

### 1. Vérifier les logs du backend

```bash
# Option 1: Avec docker (nécessite permissions)
sudo docker logs projet_encheres-backend-1 --tail 100

# Option 2: Avec le script fourni
chmod +x restart_and_check.sh
sudo ./restart_and_check.sh
```

### 2. Redémarrer les conteneurs

```bash
# Arrêter tout
docker-compose down

# Redémarrer
docker-compose up -d

# Vérifier les logs en temps réel
docker-compose logs -f backend
```

### 3. Vérifier la base de données

```bash
# Se connecter à PostgreSQL
docker exec -it projet_encheres-db-1 psql -U postgres -d encheres

# Dans psql, vérifier les tables:
\dt

# Vérifier les users
SELECT * FROM users;

# Vérifier les lots
SELECT COUNT(*) FROM lots;

# Vérifier les ventes
SELECT * FROM sales;

# Quitter
\q
```

### 4. Réinitialiser la base de données (si nécessaire)

Si les tables sont manquantes ou corrompues:

```bash
# Arrêter les conteneurs
docker-compose down

# Supprimer le volume de base de données (⚠️ PERD TOUTES LES DONNÉES)
docker volume rm projet_encheres_postgres_data

# Redémarrer
docker-compose up -d

# Attendre 10 secondes pour l'initialisation
sleep 10

# Vérifier les logs
docker-compose logs backend
```

### 5. Lancer les tests

Une fois le backend redémarré:

```bash
# Script de test complet
python3 test_api.py
```

## Scripts créés pour vous

| Script | Description |
|--------|-------------|
| `test_api.py` | Test complet de l'API (inscription, connexion, lots, ventes) |
| `test_db_connection.py` | Test de connexion à la base de données |
| `check_logs.sh` | Affiche les logs du backend |
| `restart_and_check.sh` | Redémarre et vérifie le backend |

## Utilisation après correction

### Pour scraper une vente

1. **Créer un compte admin** (si pas déjà fait):
```bash
# Se connecter à la base de données
docker exec -it projet_encheres-db-1 psql -U postgres -d encheres

# Mettre un utilisateur en admin
UPDATE users SET is_admin = true, role = 'admin' WHERE email = 'votre@email.com';
```

2. **Se connecter et récupérer le token**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "votre@email.com", "password": "votre_mot_de_passe"}
)
token = response.json()["access_token"]
print(f"Token: {token}")
```

3. **Déclencher le scraping**:
```bash
# Scraper la vente 42
curl -X POST "http://localhost:8000/api/v1/admin/scrape?sale_number=42" \
  -H "Authorization: Bearer $TOKEN"

# Scraper plusieurs ventes
curl -X POST "http://localhost:8000/api/v1/admin/scrape-multiple" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sale_numbers": [42, 43, 44, 45]}'
```

### Via le frontend

Une fois connecté en tant qu'admin, vous devriez pouvoir:
1. Accéder au dashboard admin
2. Voir la liste des ventes
3. Cliquer sur un bouton pour scraper une vente
4. Voir les statistiques de scraping

## Prochaines étapes recommandées

1. ✅ **Corriger les erreurs 500** en vérifiant les logs
2. ⬜ **Créer un utilisateur admin**
3. ⬜ **Tester le scraping** avec une vente
4. ⬜ **Ajouter une interface frontend** pour déclencher le scraping
5. ⬜ **Planifier le scraping automatique** (déjà configuré dans scheduler.py)

## Contact et Support

Si vous rencontrez des problèmes:

1. Vérifiez les logs: `sudo docker logs projet_encheres-backend-1`
2. Vérifiez que tous les conteneurs fonctionnent: `docker ps`
3. Testez la connexion DB: `nc -zv localhost 5432`
4. Vérifiez le backend: `curl http://localhost:8000/health`

## Fichiers modifiés

- ✅ `backend/app/services/scraper.py` - Scraper amélioré
- ✅ `backend/app/api/v1/endpoints/admin.py` - Nouveaux endpoints
- ✅ `test_api.py` - Tests complets
- ✅ `test_db_connection.py` - Test base de données
- ✅ `check_logs.sh` - Vérification des logs
- ✅ `restart_and_check.sh` - Redémarrage et vérification
