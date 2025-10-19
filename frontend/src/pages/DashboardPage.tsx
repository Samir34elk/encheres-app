import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Bell, TrendingDown, Eye, Package } from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

interface DashboardStats {
  total_favorites: number
  total_alerts: number
  recent_price_changes: number
  new_lots_today: number
}

interface FavoriteLot {
  id: number
  lot_number: number
  title: string
  price: number | null
  image_url: string | null
  url: string | null
  price_changed: boolean
}

interface Alert {
  id: number
  lot_id: number
  lot_title: string
  alert_type: string
  target_price: number | null
  is_active: boolean
  created_at: string
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentFavorites, setRecentFavorites] = useState<FavoriteLot[]>([])
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)

      // Fetch user's favorites
      const { data: favoritesData } = await api.get('/favorites')
      const favorites = favoritesData?.items || []
      setRecentFavorites(favorites.slice(0, 6))

      // Fetch user's alerts
      const { data: alertsData } = await api.get('/alerts')
      setActiveAlerts(alertsData?.items?.filter((a: Alert) => a.is_active) || [])

      // Calculate stats
      setStats({
        total_favorites: favorites.length,
        total_alerts: alertsData?.items?.filter((a: Alert) => a.is_active).length || 0,
        recent_price_changes: favorites.filter((f: FavoriteLot) => f.price_changed).length,
        new_lots_today: 0 // À implémenter côté backend
      })

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      toast.error('Erreur lors du chargement du tableau de bord')
    } finally {
      setLoading(false)
    }
  }

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'price_drop':
        return 'Baisse de prix'
      case 'price_below':
        return 'Prix sous seuil'
      case 'any_change':
        return 'Tout changement'
      default:
        return type
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Tableau de Bord
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Bienvenue {user?.email}
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-pink-100 text-sm font-medium">Favoris</p>
              <p className="text-4xl font-bold mt-2">{stats?.total_favorites || 0}</p>
            </div>
            <Heart className="w-12 h-12 opacity-30" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">Alertes actives</p>
              <p className="text-4xl font-bold mt-2">{stats?.total_alerts || 0}</p>
            </div>
            <Bell className="w-12 h-12 opacity-30" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm font-medium">Prix modifiés</p>
              <p className="text-4xl font-bold mt-2">{stats?.recent_price_changes || 0}</p>
            </div>
            <TrendingDown className="w-12 h-12 opacity-30" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">Nouveaux lots</p>
              <p className="text-4xl font-bold mt-2">{stats?.new_lots_today || 0}</p>
            </div>
            <Package className="w-12 h-12 opacity-30" />
          </div>
        </div>
      </div>

      {/* Recent Favorites */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Favoris récents
          </h2>
          <Link
            to="/favorites"
            className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
          >
            Voir tout →
          </Link>
        </div>

        {recentFavorites.length === 0 ? (
          <div className="text-center py-12">
            <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              Vous n'avez pas encore de favoris
            </p>
            <Link
              to="/lots"
              className="mt-4 inline-block text-blue-600 dark:text-blue-400 hover:underline"
            >
              Parcourir les lots
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentFavorites.map((lot) => (
              <Link
                key={lot.id}
                to={`/lots/${lot.id}`}
                className="group relative bg-gray-50 dark:bg-gray-700/50 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
              >
                {lot.image_url ? (
                  <img
                    src={lot.image_url}
                    alt={lot.title}
                    className="w-full h-40 object-cover"
                  />
                ) : (
                  <div className="w-full h-40 bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                    <Package className="w-12 h-12 text-gray-400" />
                  </div>
                )}

                {lot.price_changed && (
                  <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <TrendingDown className="w-3 h-3" />
                    Prix modifié
                  </div>
                )}

                <div className="p-4">
                  <h3 className="font-medium text-gray-900 dark:text-white line-clamp-2 mb-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {lot.title}
                  </h3>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      Lot #{lot.lot_number}
                    </span>
                    {lot.price && (
                      <span className="text-lg font-bold text-green-600 dark:text-green-400">
                        {lot.price.toLocaleString()} €
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Active Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Alertes actives
          </h2>
          <Link
            to="/alerts"
            className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
          >
            Gérer les alertes →
          </Link>
        </div>

        {activeAlerts.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              Vous n'avez pas d'alertes actives
            </p>
            <Link
              to="/lots"
              className="mt-4 inline-block text-blue-600 dark:text-blue-400 hover:underline"
            >
              Créer une alerte
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Bell className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {alert.lot_title}
                    </p>
                    <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                      <span>{getAlertTypeLabel(alert.alert_type)}</span>
                      {alert.target_price && (
                        <>
                          <span>•</span>
                          <span>Seuil: {alert.target_price.toLocaleString()} €</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <Link
                  to={`/lots/${alert.lot_id}`}
                  className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
                >
                  Voir le lot
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          to="/lots"
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white hover:shadow-lg transition-shadow"
        >
          <Eye className="w-8 h-8 mb-3 opacity-80" />
          <h3 className="text-lg font-semibold mb-2">Parcourir les lots</h3>
          <p className="text-blue-100 text-sm">
            Découvrez tous les lots disponibles aux enchères
          </p>
        </Link>

        <Link
          to="/favorites"
          className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-lg p-6 text-white hover:shadow-lg transition-shadow"
        >
          <Heart className="w-8 h-8 mb-3 opacity-80" />
          <h3 className="text-lg font-semibold mb-2">Mes favoris</h3>
          <p className="text-pink-100 text-sm">
            Gérez vos lots favoris et suivez leurs prix
          </p>
        </Link>

        <Link
          to="/alerts"
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white hover:shadow-lg transition-shadow"
        >
          <Bell className="w-8 h-8 mb-3 opacity-80" />
          <h3 className="text-lg font-semibold mb-2">Mes alertes</h3>
          <p className="text-green-100 text-sm">
            Configurez des alertes de prix et recevez des notifications
          </p>
        </Link>
      </div>
    </div>
  )
}
