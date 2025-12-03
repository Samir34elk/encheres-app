import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Search, Heart, ExternalLink, Filter, X, ChevronDown, ChevronUp, ArrowLeft, MapPin } from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { parseSaleMetadata } from '../utils/saleMetadata'
import { normalizeImageUrls } from '../utils/normalizeImageUrl'
import { extractTextFromHtml } from '../utils/sanitizeHtml'

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
  image_urls: string[]
  sale_id: number | null
  sale_end_date: string | null
}

interface Sale {
  id: number
  sale_number: number
  title: string
  description: string | null
  image_url?: string | null
  image_urls?: string[] | null
  status: string
  total_lots: number
  start_date?: string | null
  end_date?: string | null
}

type SortField = 'price' | 'lot_number' | 'title' | 'status' | 'depot_location' | 'end_date'
type SortOrder = 'asc' | 'desc'

export default function SaleDetailPage() {
  const { saleNumber } = useParams<{ saleNumber: string }>()
  const { isAuthenticated } = useAuthStore()
  const [sale, setSale] = useState<Sale | null>(null)
  const [lots, setLots] = useState<Lot[]>([])
  const [loading, setLoading] = useState(true)
  const [favorites, setFavorites] = useState<Set<number>>(new Set())

  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [minPrice, setMinPrice] = useState<string>('')
  const [maxPrice, setMaxPrice] = useState<string>('')
  const [selectedLocation, setSelectedLocation] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  // Display options
  const [displayLimit, setDisplayLimit] = useState<number>(1000)
  const [sortField, setSortField] = useState<SortField>('price')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const saleMetadata = useMemo(() => parseSaleMetadata(sale?.description ?? null), [sale?.description])

  const getStatusBadge = (status: string) => {
    const statuses: Record<string, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
      closed: 'bg-gray-100 text-gray-700 dark:bg-gray-700/60 dark:text-gray-300',
      upcoming: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
      cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
    }
    return statuses[status] || statuses.active
  }

  const getStatusLabel = (status: string, fallback?: string) => {
    switch (status) {
      case 'active':
        return 'Enchères en cours'
      case 'closed':
        return 'Vente clôturée'
      case 'upcoming':
        return 'Vente à venir'
      case 'cancelled':
        return 'Vente annulée'
      default:
        return fallback || status
    }
  }

  const formatDateTime = (value?: string | null) => {
    if (!value) return null
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return null

    const datePart = parsed.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
    const timePart = parsed.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
    return `${datePart} · ${timePart}`
  }

  const saleStartDate = useMemo(() => formatDateTime(sale?.start_date ?? null), [sale?.start_date])
  const saleEndDate = useMemo(() => formatDateTime(sale?.end_date ?? null), [sale?.end_date])

  // Load favorites from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('auctionFavorites')
    if (stored) {
      try {
        setFavorites(new Set(JSON.parse(stored)))
      } catch (e) {
        console.error('Failed to parse favorites:', e)
      }
    }
  }, [])

  // Fetch sale info
  useEffect(() => {
    if (saleNumber) {
      fetchSale()
    }
  }, [saleNumber])

  // Fetch lots when sale is loaded
  useEffect(() => {
    if (sale) {
      fetchLots()
    }
  }, [sale])

  const fetchSale = async () => {
    try {
      const { data } = await api.get(`/sales/by-number/${saleNumber}`)
      const image_urls = normalizeImageUrls(data.image_urls ?? data.image_url)
      setSale({
        ...data,
        image_urls,
        image_url: image_urls[0] ?? data.image_url ?? null
      })
    } catch (error) {
      console.error('Failed to fetch sale:', error)
      toast.error('Erreur lors du chargement de la vente')
    }
  }

  const fetchLots = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/lots', {
        params: {
          page: 1,
          size: 10000,
          sale_id: sale?.id,
          active_only: true
        }
      })
      const items: Lot[] = (data.items || []).map((lot: any) => {
        const image_urls = normalizeImageUrls(lot.image_urls ?? lot.image_url)
        return {
          ...lot,
          image_urls,
          image_url: image_urls[0] ?? null,
          description: lot.description ? extractTextFromHtml(lot.description) : lot.description
        }
      })
      setLots(items)
    } catch (error) {
      console.error('Failed to fetch lots:', error)
      toast.error('Erreur lors du chargement des lots')
    } finally {
      setLoading(false)
    }
  }

  // Toggle favorite
  const toggleFavorite = async (lotId: number) => {
    const newFavorites = new Set(favorites)

    if (newFavorites.has(lotId)) {
      newFavorites.delete(lotId)
    } else {
      newFavorites.add(lotId)
    }

    setFavorites(newFavorites)
    localStorage.setItem('auctionFavorites', JSON.stringify(Array.from(newFavorites)))

    if (isAuthenticated) {
      try {
        if (newFavorites.has(lotId)) {
          await api.post('/favorites', { lot_id: lotId })
        } else {
          await api.delete(`/favorites/${lotId}`)
        }
      } catch (error) {
        console.error('Failed to sync favorite:', error)
      }
    }
  }

  // Get unique locations and statuses for filters
  const uniqueLocations = useMemo(() => {
    const locations = new Set(lots.map(lot => lot.depot_location).filter(Boolean))
    return Array.from(locations).sort()
  }, [lots])

  const uniqueStatuses = useMemo(() => {
    const statuses = new Set(lots.map(lot => lot.status).filter(Boolean))
    return Array.from(statuses).sort()
  }, [lots])

  // Filter and sort lots
  const filteredLots = useMemo(() => {
    let filtered = lots.filter(lot => {
      if (searchTerm) {
        const search = searchTerm.toLowerCase()
        const matchesSearch =
          lot.title?.toLowerCase().includes(search) ||
          lot.description?.toLowerCase().includes(search) ||
          lot.lot_number?.toString().includes(search)
        if (!matchesSearch) return false
      }

      if (minPrice !== '' && lot.price !== null && lot.price < Number(minPrice)) return false
      if (maxPrice !== '' && lot.price !== null && lot.price > Number(maxPrice)) return false
      if (selectedLocation && lot.depot_location !== selectedLocation) return false
      if (selectedStatus && lot.status !== selectedStatus) return false
      if (showFavoritesOnly && !favorites.has(lot.id)) return false

      return true
    })

    filtered.sort((a, b) => {
      const fieldKey = sortField === 'end_date' ? 'sale_end_date' : sortField
      let aVal = a[fieldKey as keyof Lot]
      let bVal = b[fieldKey as keyof Lot]

      if (aVal === null || aVal === undefined) aVal = sortOrder === 'asc' ? Infinity : -Infinity
      if (bVal === null || bVal === undefined) bVal = sortOrder === 'asc' ? Infinity : -Infinity

      // Date comparison
      if (sortField === 'end_date' && typeof aVal === 'string' && typeof bVal === 'string') {
        const dateA = new Date(aVal).getTime()
        const dateB = new Date(bVal).getTime()
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })

    return filtered.slice(0, displayLimit)
  }, [lots, searchTerm, minPrice, maxPrice, selectedLocation, selectedStatus, showFavoritesOnly, favorites, sortField, sortOrder, displayLimit])

  const clearFilters = () => {
    setSearchTerm('')
    setMinPrice('')
    setMaxPrice('')
    setSelectedLocation('')
    setSelectedStatus('')
    setShowFavoritesOnly(false)
  }

  const hasActiveFilters = searchTerm || minPrice !== '' || maxPrice !== '' || selectedLocation || selectedStatus || showFavoritesOnly

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder(field === 'price' ? 'desc' : 'asc')
    }
  }

  if (loading && !sale) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <Link
          to="/sales"
          className="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour aux ventes
        </Link>

        {sale && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div className="space-y-3">
                {saleMetadata.saleType && (
                  <span className="inline-flex items-center rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary-600 dark:bg-primary-500/10 dark:text-primary-200">
                    {saleMetadata.saleType}
                  </span>
                )}
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {sale.title}
                </h1>

                <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {sale.total_lots} lot{sale.total_lots > 1 ? 's' : ''}
                  </span>
                  {saleStartDate && (
                    <>
                      <span>•</span>
                      <span>
                        Débute&nbsp;:
                        <span className="font-medium text-gray-900 dark:text-gray-100"> {saleStartDate}</span>
                      </span>
                    </>
                  )}
                  {saleEndDate && (
                    <>
                      <span>•</span>
                      <span>
                        Clôture&nbsp;:
                        <span className="font-medium text-gray-900 dark:text-gray-100"> {saleEndDate}</span>
                      </span>
                    </>
                  )}
                </div>

                {saleMetadata.organizer && (
                  <p className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <MapPin className="h-4 w-4 text-primary-500 dark:text-primary-300" />
                    <span>
                      Organisateur&nbsp;:
                      <span className="ml-1 font-semibold text-gray-900 dark:text-gray-100">
                        {saleMetadata.organizer}
                      </span>
                    </span>
                  </p>
                )}

                {saleMetadata.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {saleMetadata.tags.slice(0, 6).map(tag => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-full border border-primary-100 bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700 dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-200"
                      >
                        {tag}
                      </span>
                    ))}
                    {saleMetadata.tags.length > 6 && (
                      <span className="inline-flex items-center rounded-full border border-gray-200 bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        +{saleMetadata.tags.length - 6}
                      </span>
                    )}
                  </div>
                )}

                <p className="text-xs text-gray-500 dark:text-gray-500">
                  Référence interne&nbsp;: #{sale.sale_number}
                </p>
              </div>

              <div className="flex flex-col items-start gap-2 md:items-end">
                <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusBadge(sale.status)}`}>
                  {getStatusLabel(sale.status, saleMetadata.statusLabel)}
                </span>
                {sale.status === 'cancelled' && (
                  <span className="text-xs font-medium text-red-600 dark:text-red-400">
                    Cette vente a été signalée comme annulée par l&apos;organisateur.
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Filters bar */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 dark:text-gray-400">
            {filteredLots.length} lot{filteredLots.length > 1 ? 's' : ''} affiché{filteredLots.length > 1 ? 's' : ''} sur {lots.length}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
              showFilters
                ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/30 dark:border-blue-600'
                : 'bg-white border-gray-300 text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300'
            }`}
          >
            <Filter className="w-4 h-4" />
            Filtres
          </button>

          <label className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <input
              type="checkbox"
              checked={showFavoritesOnly}
              onChange={(e) => setShowFavoritesOnly(e.target.checked)}
              className="rounded border-gray-300 text-pink-600 focus:ring-pink-500"
            />
            <Heart className={`w-4 h-4 ${showFavoritesOnly ? 'fill-pink-500 text-pink-500' : 'text-gray-600 dark:text-gray-400'}`} />
            <span className="text-sm text-gray-700 dark:text-gray-300">Ne voir que les favoris</span>
          </label>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Recherche
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Titre, description, numéro..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Prix min (€)
              </label>
              <input
                type="number"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                placeholder="0"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Prix max (€)
              </label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="∞"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Nombre de lots
              </label>
              <select
                value={displayLimit}
                onChange={(e) => setDisplayLimit(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={50}>50 lots</option>
                <option value={100}>100 lots</option>
                <option value={500}>500 lots</option>
                <option value={1000}>1000 lots</option>
                <option value={10000}>Tous les lots</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Lieu de dépôt
              </label>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Tous les lieux</option>
                {uniqueLocations.map(loc => (
                  <option key={loc} value={loc || ''}>{loc}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Statut
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Tous les statuts</option>
                {uniqueStatuses.map(status => (
                  <option key={status} value={status || ''}>{status}</option>
                ))}
              </select>
            </div>

            {hasActiveFilters && (
              <div className="flex items-end">
                <button
                  onClick={clearFilters}
                  className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors flex items-center justify-center gap-2 text-sm"
                >
                  <X className="w-4 h-4" />
                  Réinitialiser
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredLots.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Aucun lot trouvé
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Essayez de modifier vos filtres de recherche
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900/50 sticky top-0 z-10 shadow-sm">
                <tr>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-12">
                    <Heart className="w-4 h-4" />
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('title')}
                  >
                    <div className="flex items-center gap-1">
                      Titre
                      {sortField === 'title' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('lot_number')}
                  >
                    <div className="flex items-center gap-1">
                      Lot
                      {sortField === 'lot_number' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('price')}
                  >
                    <div className="flex items-center gap-1">
                      Prix
                      {sortField === 'price' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('status')}
                  >
                    <div className="flex items-center gap-1">
                      Statut
                      {sortField === 'status' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('depot_location')}
                  >
                    <div className="flex items-center gap-1">
                      Lieu dépôt
                      {sortField === 'depot_location' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th
                    className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => handleSort('end_date')}
                  >
                    <div className="flex items-center gap-1">
                      Date de clôture
                      {sortField === 'end_date' && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    URL Lot
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    Image
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredLots.map((lot) => (
                  <TableRow
                    key={lot.id}
                    lot={lot}
                    isFavorite={favorites.has(lot.id)}
                    onToggleFavorite={toggleFavorite}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// Table Row Component (same as LotsPage for consistency)
function TableRow({
  lot,
  isFavorite,
  onToggleFavorite
}: {
  lot: Lot
  isFavorite: boolean
  onToggleFavorite: (id: number) => void
}) {
  const [showTooltip, setShowTooltip] = useState(false)
  const [showImageZoom, setShowImageZoom] = useState(false)

  return (
    <tr className="hover:bg-cyan-50 dark:hover:bg-cyan-900/10 transition-colors group">
      <td className="px-3 py-2 text-center">
        <button
          type="button"
          onClick={() => onToggleFavorite(lot.id)}
          className={`inline-flex h-8 w-8 items-center justify-center rounded-full border transition-colors ${
            isFavorite
              ? 'border-pink-200 bg-pink-50 text-pink-600 dark:border-pink-500/40 dark:bg-pink-500/10 dark:text-pink-200'
              : 'border-gray-200 bg-white text-gray-400 hover:text-pink-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500'
          }`}
          aria-label={isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
        >
          <Heart className={`h-4 w-4 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </td>

      <td
        className="px-3 py-2 relative"
        style={{ maxWidth: '450px' }}
      >
        <div
          className="relative inline-block cursor-help"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <Link
            to={`/lots/${lot.id}`}
            className="text-gray-900 dark:text-white break-words hover:text-primary-600 dark:hover:text-primary-400 transition-colors cursor-pointer"
          >
            {lot.title}
          </Link>

          {showTooltip && lot.description && lot.description !== 'N/A' && (
            <div
              className="absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50 w-96 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-xl p-3 text-sm text-gray-700 dark:text-gray-300"
              style={{
                animation: 'fadeIn 0.2s ease-in-out'
              }}
            >
              <div className="break-words whitespace-normal leading-relaxed">
                {lot.description}
              </div>
              <div className="absolute right-full top-1/2 -translate-y-1/2 border-8 border-transparent border-r-gray-300 dark:border-r-gray-600"></div>
              <div className="absolute right-full top-1/2 -translate-y-1/2 translate-x-px border-8 border-transparent border-r-white dark:border-r-gray-800"></div>
            </div>
          )}
        </div>
      </td>

      <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
        {lot.lot_number}
      </td>

      <td className="px-3 py-2">
        {lot.price !== null ? (
          <span className="font-semibold text-gray-900 dark:text-white">
            {lot.price.toLocaleString()} €
          </span>
        ) : (
          <span className="text-gray-400 text-xs">N/A</span>
        )}
      </td>

      <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
        {lot.status || 'N/A'}
      </td>

      <td
        className="px-3 py-2 text-gray-700 dark:text-gray-300 break-words"
        style={{ maxWidth: '300px' }}
      >
        {lot.depot_location || 'N/A'}
      </td>

      <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
        {lot.sale_end_date ? (
          <span className="text-sm">
            {new Date(lot.sale_end_date).toLocaleDateString('fr-FR', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric'
            })}
          </span>
        ) : (
          <span className="text-gray-400 text-xs">N/A</span>
        )}
      </td>

      <td className="px-3 py-2">
        {lot.url ? (
          <a
            href={lot.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <ExternalLink className="w-3 h-3" />
            <span className="text-xs">Voir lot</span>
          </a>
        ) : (
          <span className="text-gray-400 text-xs">N/A</span>
        )}
      </td>

      <td className="px-3 py-2">
        {lot.image_url ? (
          <div className="relative">
            <img
              src={lot.image_url}
              alt={lot.title}
              className="w-16 h-16 object-cover rounded cursor-pointer transition-transform"
              style={{
                transformOrigin: 'left center'
              }}
              onMouseEnter={() => setShowImageZoom(true)}
              onMouseLeave={() => setShowImageZoom(false)}
              onError={(e) => {
                e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle" dy=".3em"%3EImage%3C/text%3E%3C/svg%3E'
              }}
            />

            {showImageZoom && (
              <div
                className="fixed pointer-events-none z-50"
                style={{
                  left: '50%',
                  top: '50%',
                  transform: 'translate(-50%, -50%)'
                }}
              >
                <img
                  src={lot.image_url}
                  alt={lot.title}
                  className="max-w-4xl max-h-screen rounded-lg shadow-2xl border-4 border-white dark:border-gray-700"
                />
              </div>
            )}
          </div>
        ) : (
          <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center text-gray-400 text-xs">
            Ø
          </div>
        )}
      </td>
    </tr>
  )
}
