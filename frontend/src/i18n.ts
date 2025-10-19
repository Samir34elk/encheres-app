import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  en: {
    translation: {
      welcome: 'Welcome',
      login: 'Login',
      logout: 'Logout',
      register: 'Register',
      email: 'Email',
      password: 'Password',
      username: 'Username',
      dashboard: 'Dashboard',
      favorites: 'Favorites',
      alerts: 'Alerts',
      lots: 'Auction Lots',
      search: 'Search',
      filter: 'Filter',
      price: 'Price',
      status: 'Status',
      location: 'Location',
      addToFavorites: 'Add to Favorites',
      removeFromFavorites: 'Remove from Favorites',
      createAlert: 'Create Alert',
      settings: 'Settings',
      theme: 'Theme',
      language: 'Language',
    },
  },
  fr: {
    translation: {
      welcome: 'Bienvenue',
      login: 'Connexion',
      logout: 'Déconnexion',
      register: 'Inscription',
      email: 'Email',
      password: 'Mot de passe',
      username: "Nom d'utilisateur",
      dashboard: 'Tableau de bord',
      favorites: 'Favoris',
      alerts: 'Alertes',
      lots: 'Lots aux enchères',
      search: 'Rechercher',
      filter: 'Filtrer',
      price: 'Prix',
      status: 'Statut',
      location: 'Lieu',
      addToFavorites: 'Ajouter aux favoris',
      removeFromFavorites: 'Retirer des favoris',
      createAlert: 'Créer une alerte',
      settings: 'Paramètres',
      theme: 'Thème',
      language: 'Langue',
    },
  },
}

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem('language') || 'fr',
  fallbackLng: 'fr',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
