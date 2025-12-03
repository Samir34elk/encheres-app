import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Heart,
  Bell,
  ExternalLink,
  MapPin,
  Calendar,
  Eye,
  TrendingDown,
  TrendingUp,
  Minus
} from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { normalizeImageUrl } from '../utils/normalizeImageUrl'

interface Lot {
  id: number
  lot_number: number
  title: string
  description: string | null
  price: number | null
  status: string | null
  depot_location: string | null
  url: string | null
  image_url: string | null
  sale_id: number | null
  sale_end_date: string | null
  view_count: number
  favorite_count: number
  first_seen: string
  last_updated: string
  is_active: number
}

interface PriceHistory {
  id: number
  price: number
  status: string | null
  recorded_at: string
}

export default function LotDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()

  const [lot, setLot] = useState<Lot | null>(null)
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([])
  const [isFavorite, setIsFavorite] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showCreateAlert, setShowCreateAlert] = useState(false)

  // Alert form
  const [alertType, setAlertType] = useState<'price_drop' | 'price_below' | 'any_change'>('any_change')
  const [targetPrice, setTargetPrice] = useState<string>('')
  const alertTypeOptions = [
    {
      value: 'any_change',
      label: 'Nouvelle enchère ou mise à jour',
      helper: 'Soyez prévenu dès qu\'une enchère progresse ou qu\'un détail est modifié.'
    },
    {
      value: 'price_below',
      label: 'Prix sous mon budget cible',
      helper: 'Fixez un seuil et recevez une alerte tant que le lot reste abordable.'
    },
    {
      value: 'price_drop',
      label: 'Prix revu à la baisse',
      helper: 'Idéal pour les ventes dégressives ou les remises exceptionnelles.'
    }
  ] as const

  useEffect(() => {
    if (id) {
      fetchLotDetails()
      fetchPriceHistory()
    }
  }, [id])

  useEffect(() => {
    // Check if lot is favorited
    const stored = localStorage.getItem('auctionFavorites')
    if (stored && id) {
      try {
        const favorites = new Set(JSON.parse(stored))
        setIsFavorite(favorites.has(Number(id)))
      } catch (e) {
        console.error('Failed to parse favorites:', e)
      }
    }
  }, [id])

  useEffect(() => {
    if (alertType !== 'price_below') {
      setTargetPrice('')
    }
  }, [alertType])

  const fetchLotDetails = async () => {
    try {
      setLoading(true)
      const { data } = await api.get(`/lots/${id}`)
      const normalizedLot: Lot = {
        ...data,
        image_url: normalizeImageUrl(data.image_url)
      }
      setLot(normalizedLot)
    } catch (error) {
      console.error('Failed to fetch lot details:', error)
      toast.error('Erreur lors du chargement du lot')
    } finally {
      setLoading(false)
    }
  }

  const fetchPriceHistory = async () => {
    try {
      const { data } = await api.get(`/lots/${id}/price-history`)
      setPriceHistory(data || [])
    } catch (error) {
      console.error('Failed to fetch price history:', error)
    }
  }

  const toggleFavorite = async () => {
    if (!lot) return

    const newFavoriteState = !isFavorite
    setIsFavorite(newFavoriteState)

    // Update localStorage
    const stored = localStorage.getItem('auctionFavorites')
    const favorites = stored ? new Set(JSON.parse(stored)) : new Set()

    if (newFavoriteState) {
      favorites.add(lot.id)
    } else {
      favorites.delete(lot.id)
    }

    localStorage.setItem('auctionFavorites', JSON.stringify(Array.from(favorites)))

    // Sync with backend if authenticated
    if (isAuthenticated) {
      try {
        if (newFavoriteState) {
          await api.post('/favorites', { lot_id: lot.id })
          toast.success('Ajouté aux favoris')
        } else {
          await api.delete(`/favorites/${lot.id}`)
          toast.success('Retiré des favoris')
        }
      } catch (error) {
        console.error('Failed to sync favorite:', error)
        toast.error('Erreur lors de la synchronisation')
      }
    }
  }

  const handleCreateAlert = async () => {
    if (!lot || !isAuthenticated) {
      toast.error('Vous devez être connecté pour créer une alerte')
      navigate('/login')
      return
    }

    if (alertType === 'price_below' && !targetPrice) {
      toast.error('Indiquez votre budget cible pour cette alerte')
      return
    }

    try {
      await api.post('/alerts', {
        lot_id: lot.id,
        alert_type: alertType,
        target_price: alertType === 'price_below' && targetPrice ? Number(targetPrice) : null
      })
      toast.success('Alerte créée avec succès')
      setShowCreateAlert(false)
      setTargetPrice('')
    } catch (error) {
      console.error('Failed to create alert:', error)
      toast.error('Erreur lors de la création de l\'alerte')
    }
  }

  // Price trend calculation
  const getPriceTrend = () => {
    if (priceHistory.length < 2) return null

    const latest = priceHistory[0].price
    const previous = priceHistory[1].price
    const change = latest - previous
    const changePercent = ((change / previous) * 100).toFixed(1)

    return {
      change,
      changePercent,
      trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable'
    }
  }

  const priceTrend = getPriceTrend()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!lot) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Lot non trouvé
        </h2>
        <Link
          to="/lots"
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          Retour aux lots
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/lots"
          className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour aux lots
        </Link>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={toggleFavorite}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${
              isFavorite
                ? 'bg-pink-50 border-pink-200 text-pink-700 dark:bg-pink-900/20 dark:border-pink-600 dark:text-pink-300'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
            }`}
          >
            <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
            <span className="hidden sm:inline">{isFavorite ? 'Favori' : 'Favoris'}</span>
          </button>

          <button
            onClick={() => setShowCreateAlert(!showCreateAlert)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">Alerte</span>
          </button>

          {lot.url && (
            <a
              href={lot.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              <span className="hidden sm:inline">Site officiel</span>
            </a>
          )}
        </div>
      </div>

      {/* Create Alert Panel */}
      {showCreateAlert && (
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Créer une alerte pour ce lot
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Type d'alerte
              </label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value as 'price_drop' | 'price_below' | 'any_change')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {alertTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {alertTypeOptions.find(option => option.value === alertType)?.helper}
              </p>
            </div>

            {alertType === 'price_below' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Budget cible (€)
                </label>
                <input
                  type="number"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  placeholder="Ex: 5000"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            )}

            <div className="flex items-end">
              <button
                onClick={handleCreateAlert}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Créer l'alerte
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Image and Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Image */}
          {lot.image_url && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <img
                src={lot.image_url}
                alt={lot.title}
                className="w-full h-auto max-h-96 object-contain"
                onError={(e) => {
                  e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="400"%3E%3Crect fill="%23ddd" width="800" height="400"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em" font-size="24"%3EImage non disponible%3C/text%3E%3C/svg%3E'
                }}
              />
            </div>
          )}

          {/* Description */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              {lot.title}
            </h2>

            {lot.description && lot.description !== 'N/A' ? (
              <div className="prose dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {lot.description}
                </p>
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 italic">
                Aucune description disponible
              </p>
            )}
          </div>

          {/* Price History Chart */}
          {priceHistory.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Historique des prix
              </h3>
              <PriceHistoryChart history={priceHistory} />

              {/* Price History Table */}
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900/50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Date
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Prix
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Statut
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Évolution
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {priceHistory.map((entry, index) => {
                      const prevPrice = index < priceHistory.length - 1 ? priceHistory[index + 1].price : null
                      const change = prevPrice ? entry.price - prevPrice : 0

                      return (
                        <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
                            {new Date(entry.recorded_at).toLocaleString('fr-FR')}
                          </td>
                          <td className="px-3 py-2 font-semibold text-gray-900 dark:text-white">
                            {entry.price.toLocaleString()} €
                          </td>
                          <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
                            {entry.status || 'N/A'}
                          </td>
                          <td className="px-3 py-2">
                            {change !== 0 && (
                              <span className={`flex items-center gap-1 ${
                                change > 0
                                  ? 'text-red-600 dark:text-red-400'
                                  : 'text-green-600 dark:text-green-400'
                              }`}>
                                {change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                {Math.abs(change).toLocaleString()} €
                              </span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Info Cards */}
        <div className="space-y-6">
          {/* Price Card */}
          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-lg p-6 text-white">
            <div className="text-sm font-medium mb-2 opacity-90">Prix actuel</div>
            {lot.price !== null ? (
              <>
                <div className="text-4xl font-bold mb-2">
                  {lot.price.toLocaleString()} €
                </div>
                {priceTrend && (
                  <div className={`flex items-center gap-2 text-sm ${
                    priceTrend.trend === 'down' ? 'text-green-100' : 'text-red-100'
                  }`}>
                    {priceTrend.trend === 'up' && <TrendingUp className="w-4 h-4" />}
                    {priceTrend.trend === 'down' && <TrendingDown className="w-4 h-4" />}
                    {priceTrend.trend === 'stable' && <Minus className="w-4 h-4" />}
                    {priceTrend.trend !== 'stable' && (
                      <span>
                        {priceTrend.change > 0 ? '+' : ''}{priceTrend.change.toLocaleString()} € ({priceTrend.changePercent}%)
                      </span>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="text-2xl opacity-75">Prix non disponible</div>
            )}
          </div>

          {/* Lot Info Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Informations
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Lot N°</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  #{lot.lot_number}
                </span>
              </div>

              {lot.status && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Statut</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {lot.status}
                  </span>
                </div>
              )}

              {lot.depot_location && (
                <div className="flex items-start justify-between">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    Lieu
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white text-right max-w-[60%]">
                    {lot.depot_location}
                  </span>
                </div>
              )}

              {lot.sale_end_date && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Date de clôture
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {new Date(lot.sale_end_date).toLocaleDateString('fr-FR', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  Vues
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {lot.view_count}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Heart className="w-4 h-4" />
                  Favoris
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {lot.favorite_count}
                </span>
              </div>

              <div className="flex items-start justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Première apparition
                </span>
                <span className="font-medium text-gray-900 dark:text-white text-right text-xs">
                  {new Date(lot.first_seen).toLocaleDateString('fr-FR')}
                </span>
              </div>

              <div className="flex items-start justify-between">
                <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Dernière MAJ
                </span>
                <span className="font-medium text-gray-900 dark:text-white text-right text-xs">
                  {new Date(lot.last_updated).toLocaleString('fr-FR')}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Simple Price History Chart Component
function PriceHistoryChart({ history }: { history: PriceHistory[] }) {
  if (history.length === 0) return null

  const prices = history.map(h => h.price).reverse()
  const maxPrice = Math.max(...prices)
  const minPrice = Math.min(...prices)
  const priceRange = maxPrice - minPrice || 1

  const width = 800
  const height = 200
  const padding = 40

  // Generate SVG path
  const points = prices.map((price, index) => {
    const x = padding + (index * (width - 2 * padding)) / (prices.length - 1 || 1)
    const y = height - padding - ((price - minPrice) / priceRange) * (height - 2 * padding)
    return `${x},${y}`
  })

  const pathD = `M ${points.join(' L ')}`

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        style={{ maxHeight: '300px' }}
      >
        {/* Grid lines */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke="currentColor"
          strokeWidth="1"
          className="text-gray-300 dark:text-gray-600"
        />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="currentColor"
          strokeWidth="1"
          className="text-gray-300 dark:text-gray-600"
        />

        {/* Price line */}
        <path
          d={pathD}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-green-600 dark:text-green-400"
        />

        {/* Data points */}
        {points.map((point, index) => {
          const [x, y] = point.split(',').map(Number)
          return (
            <circle
              key={index}
              cx={x}
              cy={y}
              r="4"
              fill="currentColor"
              className="text-green-600 dark:text-green-400"
            >
              <title>{prices[index].toLocaleString()} €</title>
            </circle>
          )
        })}

        {/* Y-axis labels */}
        <text
          x={padding - 10}
          y={padding}
          textAnchor="end"
          fontSize="12"
          className="fill-gray-600 dark:fill-gray-400"
        >
          {maxPrice.toLocaleString()} €
        </text>
        <text
          x={padding - 10}
          y={height - padding}
          textAnchor="end"
          fontSize="12"
          className="fill-gray-600 dark:fill-gray-400"
        >
          {minPrice.toLocaleString()} €
        </text>
      </svg>
    </div>
  )
}
