import { useState, useEffect } from 'react'
import {
  Play,
  RefreshCw,
  Users,
  Package,
  TrendingUp,
  Database,
  Calendar,
  Activity,
  BarChart3
} from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

interface Stats {
  total_users: number
  total_lots: number
  total_sales: number
  active_lots: number
  total_favorites: number
  total_alerts: number
  last_scrape: string | null
  scraper_status: string
}

interface ScraperLog {
  id: number
  sale_number: number
  lots_scraped: number
  status: string
  error: string | null
  started_at: string
  completed_at: string | null
}

export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [logs, setLogs] = useState<ScraperLog[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [saleNumber, setSaleNumber] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)

      // Fetch stats
      const { data: statsData } = await api.get('/admin/stats')
      setStats(statsData)

      // Fetch scraper logs
      const { data: logsData } = await api.get('/admin/scraper-logs', {
        params: { page: 1, size: 10 }
      })
      setLogs(logsData?.items || [])

    } catch (error) {
      console.error('Failed to fetch admin data:', error)
      toast.error('Erreur lors du chargement des données admin')
    } finally {
      setLoading(false)
    }
  }

  const startScraper = async () => {
    if (!saleNumber) {
      toast.error('Veuillez entrer un numéro de vente')
      return
    }

    try {
      setScraping(true)
      await api.post('/admin/scrape', {
        sale_number: Number(saleNumber)
      })
      toast.success(`Scraper lancé pour la vente ${saleNumber}`)
      setSaleNumber('')

      // Refresh data after a delay
      setTimeout(() => {
        fetchData()
      }, 3000)
    } catch (error: any) {
      console.error('Failed to start scraper:', error)
      toast.error(error.response?.data?.detail || 'Erreur lors du lancement du scraper')
    } finally {
      setScraping(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'running':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'failed':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Terminé'
      case 'running':
        return 'En cours'
      case 'failed':
        return 'Échoué'
      default:
        return status
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
          Administration
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Gérez le système et lancez le scraper
        </p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm font-medium">Utilisateurs</p>
                <p className="text-4xl font-bold mt-2">{stats.total_users}</p>
              </div>
              <Users className="w-12 h-12 opacity-30" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm font-medium">Lots totaux</p>
                <p className="text-4xl font-bold mt-2">{stats.total_lots}</p>
                <p className="text-green-100 text-xs mt-1">{stats.active_lots} actifs</p>
              </div>
              <Package className="w-12 h-12 opacity-30" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm font-medium">Ventes</p>
                <p className="text-4xl font-bold mt-2">{stats.total_sales}</p>
              </div>
              <TrendingUp className="w-12 h-12 opacity-30" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl p-6 text-white shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-pink-100 text-sm font-medium">Favoris</p>
                <p className="text-4xl font-bold mt-2">{stats.total_favorites}</p>
                <p className="text-pink-100 text-xs mt-1">{stats.total_alerts} alertes</p>
              </div>
              <Activity className="w-12 h-12 opacity-30" />
            </div>
          </div>
        </div>
      )}

      {/* Scraper Control */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Contrôle du Scraper
          </h2>
        </div>

        {stats?.last_scrape && (
          <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-gray-600 dark:text-gray-400">
                Dernier scraping :
              </span>
              <span className="font-medium text-gray-900 dark:text-white">
                {new Date(stats.last_scrape).toLocaleString('fr-FR')}
              </span>
              <span className={`ml-auto px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(stats.scraper_status)}`}>
                {getStatusLabel(stats.scraper_status)}
              </span>
            </div>
          </div>
        )}

        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Numéro de vente
            </label>
            <input
              type="number"
              value={saleNumber}
              onChange={(e) => setSaleNumber(e.target.value)}
              placeholder="Ex: 12024"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={scraping}
            />
          </div>

          <button
            onClick={startScraper}
            disabled={scraping || !saleNumber}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {scraping ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                En cours...
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Lancer le scraping
              </>
            )}
          </button>

          <button
            onClick={fetchData}
            disabled={scraping}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 transition-colors"
            title="Rafraîchir les données"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-900 dark:text-blue-300">
            <strong>ℹ️ Info :</strong> Le scraper va récupérer tous les lots de la vente spécifiée
            depuis le site encheres-domaine.com et les stocker dans la base de données.
            Cela peut prendre plusieurs minutes selon le nombre de lots.
          </p>
        </div>
      </div>

      {/* Scraper Logs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Historique du Scraper
          </h2>
        </div>

        {logs.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400">
              Aucun log de scraping disponible
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Vente
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Lots récupérés
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Statut
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Début
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Fin
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    Erreur
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-gray-900 dark:text-white font-medium">
                      #{log.sale_number}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {log.lots_scraped}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(log.status)}`}>
                        {getStatusLabel(log.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {new Date(log.started_at).toLocaleString('fr-FR', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                      {log.completed_at
                        ? new Date(log.completed_at).toLocaleString('fr-FR', {
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {log.error ? (
                        <span className="text-red-600 dark:text-red-400 text-xs">
                          {log.error.length > 50 ? log.error.substring(0, 50) + '...' : log.error}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Database className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Taux de couverture
            </h3>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {stats ? Math.round((stats.active_lots / stats.total_lots) * 100) : 0}%
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Lots actifs / Total
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <Activity className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Engagement utilisateurs
            </h3>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {stats ? Math.round((stats.total_favorites / stats.total_users) * 10) / 10 : 0}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Favoris par utilisateur
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Lots par vente
            </h3>
          </div>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">
            {stats && stats.total_sales > 0 ? Math.round(stats.total_lots / stats.total_sales) : 0}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Moyenne par vente
          </p>
        </div>
      </div>
    </div>
  )
}
