import { useState, useEffect, useMemo } from 'react'
import { Search, Heart, ExternalLink, Filter, X, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

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
}

type SortField = 'price' | 'lot_number' | 'title' | 'status' | 'depot_location'
type SortOrder = 'asc' | 'desc'

export default function LotsPage() {
  const { isAuthenticated } = useAuthStore()
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

  // Fetch all lots
  useEffect(() => {
    const fetchLots = async () => {
      try {
        setLoading(true)
        const { data } = await api.get('/lots', {
          params: {
            page: 1,
            size: 10000, // Get all lots
            active_only: true
          }
        })
        setLots(data.items || [])
      } catch (error) {
        console.error('Failed to fetch lots:', error)
        toast.error('Erreur lors du chargement des enchères')
      } finally {
        setLoading(false)
      }
    }

    fetchLots()
  }, [])

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

    // Sync with backend if authenticated
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
      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase()
        const matchesSearch =
          lot.title?.toLowerCase().includes(search) ||
          lot.description?.toLowerCase().includes(search) ||
          lot.lot_number?.toString().includes(search)
        if (!matchesSearch) return false
      }

      // Price filters
      if (minPrice !== '' && lot.price !== null && lot.price < Number(minPrice)) return false
      if (maxPrice !== '' && lot.price !== null && lot.price > Number(maxPrice)) return false

      // Location filter
      if (selectedLocation && lot.depot_location !== selectedLocation) return false

      // Status filter
      if (selectedStatus && lot.status !== selectedStatus) return false

      // Favorites filter
      if (showFavoritesOnly && !favorites.has(lot.id)) return false

      return true
    })

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField]
      let bVal = b[sortField]

      // Handle null values
      if (aVal === null) aVal = sortOrder === 'asc' ? Infinity : -Infinity
      if (bVal === null) bVal = sortOrder === 'asc' ? Infinity : -Infinity

      // String comparison
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      // Numeric comparison
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })

    // Apply display limit
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Liste des Enchères
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
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

            {/* Min Price */}
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

            {/* Max Price */}
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

            {/* Display limit */}
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

            {/* Location */}
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

            {/* Status */}
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

            {/* Clear filters */}
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
      {filteredLots.length === 0 ? (
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
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    URL Lot
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">
                    URL Image
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

// Table Row Component with tooltip and image hover
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
      {/* Favorite */}
      <td className="px-3 py-2 text-center">
        <input
          type="checkbox"
          checked={isFavorite}
          onChange={() => onToggleFavorite(lot.id)}
          className="w-4 h-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500 cursor-pointer"
        />
      </td>

      {/* Title with Tooltip */}
      <td
        className="px-3 py-2 relative"
        style={{ maxWidth: '450px' }}
      >
        <div
          className="relative inline-block cursor-help"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <span className="text-gray-900 dark:text-white break-words">
            {lot.title}
          </span>

          {/* Tooltip - Positioned to the right */}
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
              {/* Arrow pointing left */}
              <div className="absolute right-full top-1/2 -translate-y-1/2 border-8 border-transparent border-r-gray-300 dark:border-r-gray-600"></div>
              <div className="absolute right-full top-1/2 -translate-y-1/2 translate-x-px border-8 border-transparent border-r-white dark:border-r-gray-800"></div>
            </div>
          )}
        </div>
      </td>

      {/* Lot Number */}
      <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
        {lot.lot_number}
      </td>

      {/* Price */}
      <td className="px-3 py-2">
        {lot.price !== null ? (
          <span className="font-semibold text-gray-900 dark:text-white">
            {lot.price.toLocaleString()} €
          </span>
        ) : (
          <span className="text-gray-400 text-xs">N/A</span>
        )}
      </td>

      {/* Status */}
      <td className="px-3 py-2 text-gray-700 dark:text-gray-300">
        {lot.status || 'N/A'}
      </td>

      {/* Depot Location */}
      <td
        className="px-3 py-2 text-gray-700 dark:text-gray-300 break-words"
        style={{ maxWidth: '300px' }}
      >
        {lot.depot_location || 'N/A'}
      </td>

      {/* URL Lot */}
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

      {/* URL Image with zoom on hover */}
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

            {/* Zoomed image overlay */}
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
