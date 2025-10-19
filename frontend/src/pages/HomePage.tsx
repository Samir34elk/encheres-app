import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Search, Bell, Heart, BarChart3 } from 'lucide-react'

export default function HomePage() {
  const { t } = useTranslation()

  const features = [
    {
      icon: <Search className="w-12 h-12 text-primary-600" />,
      title: 'Recherche Avancée',
      description: 'Recherchez parmi tous les lots avec des filtres puissants',
    },
    {
      icon: <Bell className="w-12 h-12 text-primary-600" />,
      title: 'Alertes Personnalisées',
      description: 'Recevez des notifications pour les changements de prix et nouveaux lots',
    },
    {
      icon: <Heart className="w-12 h-12 text-primary-600" />,
      title: 'Favoris',
      description: 'Sauvegardez vos lots préférés et ajoutez des notes',
    },
    {
      icon: <BarChart3 className="w-12 h-12 text-primary-600" />,
      title: 'Statistiques',
      description: 'Visualisez l\'évolution des prix et les tendances',
    },
  ]

  return (
    <div>
      {/* Hero Section */}
      <section className="text-center py-20">
        <h1 className="text-5xl font-bold mb-6 text-gray-900 dark:text-white">
          {t('welcome')} - Enchères du Domaine
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
          Suivez les enchères du domaine public en temps réel. Recevez des alertes,
          gérez vos favoris et ne manquez aucune opportunité.
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            to="/lots"
            className="bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition"
          >
            Voir les Lots
          </Link>
          <Link
            to="/register"
            className="bg-white dark:bg-gray-800 text-primary-600 dark:text-primary-400 px-8 py-3 rounded-lg font-semibold border-2 border-primary-600 hover:bg-primary-50 dark:hover:bg-gray-700 transition"
          >
            S'inscrire
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900 dark:text-white">
          Fonctionnalités
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md text-center hover:shadow-lg transition"
            >
              <div className="flex justify-center mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-primary-600 dark:bg-primary-800 text-white rounded-lg">
        <div className="grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold mb-2">15min</div>
            <div className="text-primary-100">Mise à jour automatique</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">24/7</div>
            <div className="text-primary-100">Surveillance continue</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">100%</div>
            <div className="text-primary-100">Gratuit et Open Source</div>
          </div>
        </div>
      </section>
    </div>
  )
}
