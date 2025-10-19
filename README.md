# Enchères du Domaine - Application Web

Application web moderne de suivi des enchères du domaine public français.

## 🚀 Fonctionnalités

### ✨ Interface Utilisateur Moderne
- **Affichage de TOUS les lots** sans pagination (choix de 50/100/500/1000/tous)
- **2 modes d'affichage** : Vue tableau et vue grille
- **Filtres temps réel** : recherche, prix min/max, lieu, statut
- **Tri multi-colonnes** : prix, numéro, popularité, date
- **Dark mode** intégré
- **Responsive** sur tous les appareils

### 💝 Système de Favoris
- Marquer des lots en favoris (localStorage + sync backend)
- Filtre "favoris uniquement"
- Compteur de favoris en temps réel

### 📊 Statistiques en Direct
- Total de lots affichés
- Prix moyen des lots visibles
- Prix maximum
- Nombre de favoris

### 🖼️ Fonctionnalités Visuelles
- **Zoom d'image au survol** (vue tableau)
- **Tooltips de description** au hover
- **Animations fluides** et transitions
- **Design professionnel** avec Tailwind CSS

### 🔐 Fonctionnalités Avancées (Authentification requise)
- Dashboard personnel
- Alertes de prix
- Notifications
- Historique des enchères
- Commentaires sur les lots

## 🛠️ Stack Technique

### Frontend
- **React 18** + **TypeScript**
- **Vite** (build ultra-rapide)
- **Tailwind CSS** (design moderne)
- **Zustand** (state management)
- **React Router** (navigation)
- **Axios** (API calls)
- **Lucide React** (icônes)

### Backend
- **FastAPI** (Python)
- **SQLAlchemy** (ORM)
- **PostgreSQL** (base de données)
- **Playwright** (scraping)
- **APScheduler** (tâches planifiées)

## 📦 Installation

### Prérequis
- Node.js 18+
- Python 3.12+
- PostgreSQL

### Frontend

```bash
cd frontend
npm install

# Créer le fichier .env
cp .env.example .env

# Lancer en développement
npm run dev

# Builder pour production
npm run build
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Configurer la base de données dans .env
# Lancer le serveur
python -m app.main
```

## 🎯 Utilisation

1. **Sans compte** : Visualiser tous les lots, filtrer, trier, marquer des favoris (localStorage)
2. **Avec compte gratuit** : Sync des favoris, alertes, notifications
3. **Abonnement premium** : Alertes avancées, export CSV/PDF, statistiques détaillées

## 📱 Screenshots

### Vue Tableau (1000 lots)
- Tous les lots visibles d'un coup
- Tri instantané sur toutes les colonnes
- Filtres temps réel sans rechargement

### Vue Grille
- Design moderne en cartes
- Images grandes et lisibles
- Informations essentielles accessibles

## 🚀 Différences avec encheres.html

L'ancienne version `encheres.html` était un fichier HTML standalone avec DataTables.

La nouvelle version React apporte :
- ✅ Design moderne et professionnel
- ✅ Authentification et comptes utilisateurs
- ✅ Synchronisation backend des favoris
- ✅ Alertes et notifications
- ✅ Historique des prix
- ✅ Système de commentaires
- ✅ Export de données
- ✅ Dashboard personnalisé
- ✅ Mode sombre
- ✅ Responsive mobile
- ✅ Performance optimisée (React virtualization possible)

## 🔧 Configuration

### Variables d'environnement Frontend

```env
VITE_API_URL=http://localhost:8000/api/v1
```

### Variables d'environnement Backend

Voir `backend/.env.example`

## 📄 Licence

Projet personnel - Tous droits réservés

## 🤝 Contribution

Ce projet est actuellement en développement privé.

---

**Développé avec ❤️ pour une expérience utilisateur exceptionnelle**
