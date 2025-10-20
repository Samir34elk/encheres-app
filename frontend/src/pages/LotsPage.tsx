import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Search, Heart, ExternalLink, Filter, X, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'
import { parseSaleMetadata } from '../utils/saleMetadata'

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
}

type SortField = 'price' | 'lot_number' | 'title' | 'status' | 'depot_location' | 'end_date'
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
  const [selectedSaleIds, setSelectedSaleIds] = useState<number[]>([])

  // Display options
  const displayOptions = [50, 100, 500, 1000, 10000]

  const [displayLimit, setDisplayLimit] = useState<number>(100)
  const [displayPage, setDisplayPage] = useState<number>(1)
  const [sortField, setSortField] = useState<SortField>('price')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [salesMetadata, setSalesMetadata] = useState<Record<number, { title: string; saleNumber: number; tags: string[] }>>({})
  const [loadingSalesMetadata, setLoadingSalesMetadata] = useState(false)

  // Load favorites from backend (if authenticated) and merge with localStorage
  useEffect(() => {
    const loadFavorites = async () => {
      // Load localStorage favorites first
      const stored = localStorage.getItem('auctionFavorites')
      let localFavorites = new Set<number>()
      if (stored) {
        try {
          localFavorites = new Set(JSON.parse(stored))
        } catch (e) {
          console.error('Failed to parse favorites:', e)
        }
      }

      // Try to load from backend if authenticated
      try {
        const { data } = await api.get('/favorites', {
          headers: { 'X-Skip-Auth-Redirect': 'true' }
        })
        // Merge backend favorites with local ones
        const backendFavoriteIds = data.items.map((item: any) => item.lot_id)
        const mergedFavorites = new Set([...localFavorites, ...backendFavoriteIds])
        setFavorites(mergedFavorites)
        // Update localStorage with merged favorites
        localStorage.setItem('auctionFavorites', JSON.stringify(Array.from(mergedFavorites)))
      } catch (error) {
        // If not authenticated or error, just use local favorites
        setFavorites(localFavorites)
      }
    }

    loadFavorites()
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

  useEffect(() => {
    const fetchSalesMetadata = async () => {
      try {
        setLoadingSalesMetadata(true)
        const metadata: Record<number, { title: string; saleNumber: number; tags: string[] }> = {}
        let currentPage = 1
        const pageSize = 100
        let totalPages = 1

        while (currentPage <= totalPages) {
          const { data } = await api.get('/sales', {
            params: { page: currentPage, size: pageSize }
          })
          const items = data.items || []
          totalPages = data.pages || 1

          for (const sale of items) {
            if (sale.status === 'cancelled') continue
            const parsed = parseSaleMetadata(sale.description)
            metadata[sale.id] = {
              title: sale.title,
              saleNumber: sale.sale_number,
              tags: parsed.tags
            }
          }

          currentPage += 1
        }

        setSalesMetadata(metadata)
      } catch (error) {
        console.error('Failed to fetch sales metadata:', error)
        toast.error('Impossible de charger les informations de ventes')
      } finally {
        setLoadingSalesMetadata(false)
      }
    }

    fetchSalesMetadata()
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

  const availableSaleOptions = useMemo(() => {
    const idsInLots = new Set<number>()
    lots.forEach(lot => {
      if (lot.sale_id) idsInLots.add(lot.sale_id)
    })

    return Array.from(idsInLots)
      .map(id => {
        const meta = salesMetadata[id]
        const label = meta?.title || `Vente #${meta?.saleNumber ?? id}`
        return {
          id,
          label,
          tags: meta?.tags || []
        }
      })
      .filter(option => option.label)
      .sort((a, b) => a.label.localeCompare(b.label, 'fr'))
  }, [lots, salesMetadata])

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

      if (selectedSaleIds.length > 0) {
        if (!lot.sale_id || !selectedSaleIds.includes(lot.sale_id)) return false
      }

      // Favorites filter
      if (showFavoritesOnly && !favorites.has(lot.id)) return false

      return true
    })

    // Sort
    filtered.sort((a, b) => {
      // Map end_date to sale_end_date
      const fieldKey = sortField === 'end_date' ? 'sale_end_date' : sortField
      let aVal = a[fieldKey as keyof Lot]
      let bVal = b[fieldKey as keyof Lot]

      // Handle null values
      if (aVal === null || aVal === undefined) aVal = sortOrder === 'asc' ? Infinity : -Infinity
      if (bVal === null || bVal === undefined) bVal = sortOrder === 'asc' ? Infinity : -Infinity

      // Date comparison
      if (sortField === 'end_date' && typeof aVal === 'string' && typeof bVal === 'string') {
        const dateA = new Date(aVal).getTime()
        const dateB = new Date(bVal).getTime()
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA
      }

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

    return filtered
  }, [lots, searchTerm, minPrice, maxPrice, selectedLocation, selectedStatus, selectedSaleIds, showFavoritesOnly, favorites, salesMetadata, sortField, sortOrder])

  const totalFilteredLots = filteredLots.length
  const totalPages = Math.max(1, Math.ceil(totalFilteredLots / displayLimit))
  const baseCountLabel =
    totalFilteredLots !== lots.length ? ` (sur ${lots.length} lots indexés)` : ''

  const paginatedLots = useMemo(() => {
    const startIndex = (displayPage - 1) * displayLimit
    return filteredLots.slice(startIndex, startIndex + displayLimit)
  }, [filteredLots, displayLimit, displayPage])

  useEffect(() => {
    setDisplayPage(1)
  }, [searchTerm, minPrice, maxPrice, selectedLocation, selectedStatus, showFavoritesOnly, selectedSaleIds, displayLimit])

  useEffect(() => {
    if (displayPage > totalPages) {
      setDisplayPage(totalPages)
    }
  }, [displayPage, totalPages])

  const clearFilters = () => {
    setSearchTerm('')
    setMinPrice('')
    setMaxPrice('')
    setSelectedLocation('')
    setSelectedStatus('')
    setShowFavoritesOnly(false)
    setSelectedSaleIds([])
  }

  const hasActiveFilters =
    searchTerm ||
    minPrice !== '' ||
    maxPrice !== '' ||
    selectedLocation ||
    selectedStatus ||
    showFavoritesOnly ||
    selectedSaleIds.length > 0

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
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Liste des Enchères
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {paginatedLots.length} lot{paginatedLots.length > 1 ? 's' : ''} affiché{paginatedLots.length > 1 ? 's' : ''} sur {totalFilteredLots} résultat{totalFilteredLots > 1 ? 's' : ''}{baseCountLabel}
          </p>
        </div>

        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <div className="group flex items-center gap-0 rounded-full border border-gray-200 bg-white px-2 py-1 shadow-sm transition-all duration-700 ease-in-out hover:shadow-lg dark:border-gray-700 dark:bg-gray-800 md:gap-3">
            <div className="flex items-center gap-0 group-hover:gap-2">
              {displayOptions.map(option => {
                const isActive = displayLimit === option
                const label = option === 10000 ? 'Tous' : option
                return (
                  <button
                    key={option}
                    type="button"
                    onClick={() => {
                      setDisplayLimit(option)
                      setDisplayPage(1)
                    }}
                    className={`rounded-full px-3 py-1 text-xs font-semibold transition-all duration-700 ease-in-out ${
                      isActive
                        ? 'inline-flex bg-primary-600 text-white shadow-sm'
                        : 'hidden group-hover:inline-flex text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                    }`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
            <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              lots / page
            </span>
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

            <button
              onClick={() => setShowFavoritesOnly(prev => !prev)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                showFavoritesOnly
                  ? 'border-pink-200 bg-pink-50 text-pink-600 dark:border-pink-500/50 dark:bg-pink-500/10 dark:text-pink-200'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              <input
                type="checkbox"
                checked={showFavoritesOnly}
                onChange={(e) => setShowFavoritesOnly(e.target.checked)}
                className="sr-only"
              />
              <Heart className={`w-4 h-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
              <span className="text-sm">Ne voir que les favoris</span>
            </button>
          </div>
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

            {/* Price range */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Prix
              </label>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <div className="flex flex-1 items-center rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-200 dark:border-gray-600 dark:bg-gray-700 dark:focus-within:border-primary-400 dark:focus-within:ring-primary-700/30">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Min
                  </span>
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value.replace(/[^0-9]/g, ''))}
                    placeholder="0"
                    className="ml-2 w-full bg-transparent text-sm text-gray-900 outline-none dark:text-white"
                  />
                </div>
                <span className="hidden text-xs font-semibold uppercase tracking-wide text-gray-400 sm:inline dark:text-gray-500">
                  à
                </span>
                <div className="flex flex-1 items-center rounded-lg border border-gray-300 bg-white px-3 py-2 shadow-sm focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-200 dark:border-gray-600 dark:bg-gray-700 dark:focus-within:border-primary-400 dark:focus-within:ring-primary-700/30">
                  <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                    Max
                  </span>
                  <input
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value.replace(/[^0-9]/g, ''))}
                    placeholder="Illimité"
                    className="ml-2 w-full bg-transparent text-sm text-gray-900 outline-none dark:text-white"
                  />
                </div>
              </div>
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

            {/* Sales filter */}
            <div className="lg:col-span-5">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Ventes
              </label>
              <div className="flex flex-wrap gap-2">
                {loadingSalesMetadata && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">Chargement…</span>
                )}
                {!loadingSalesMetadata && availableSaleOptions.length === 0 && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">Aucune vente active détectée</span>
                )}
                {availableSaleOptions.map(({ id, label }) => {
                  const isActive = selectedSaleIds.includes(id)
                  return (
                    <button
                      key={id}
                      type="button"
                      onClick={() =>
                        setSelectedSaleIds(prev =>
                          prev.includes(id)
                            ? prev.filter(value => value !== id)
                            : [...prev, id]
                        )
                      }
                      className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                        isActive
                          ? 'bg-primary-600 text-white shadow-sm'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
              {selectedSaleIds.length > 0 && (
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  {selectedSaleIds.length} vente{selectedSaleIds.length > 1 ? 's' : ''} sélectionnée{selectedSaleIds.length > 1 ? 's' : ''}.
                </p>
              )}
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
      {totalFilteredLots === 0 ? (
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
          <div className="flex flex-col gap-3 border-b border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-300 md:flex-row md:items-center md:justify-between">
            <span>
              Page {displayPage} sur {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setDisplayPage(p => Math.max(1, p - 1))}
                disabled={displayPage === 1}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition disabled:cursor-not-allowed disabled:opacity-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                Précédent
              </button>
              <button
                onClick={() => setDisplayPage(p => Math.min(totalPages, p + 1))}
                disabled={displayPage === totalPages}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition disabled:cursor-not-allowed disabled:opacity-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                Suivant
              </button>
            </div>
          </div>
          <div className="hidden md:block overflow-x-auto">
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
                    URL Image
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {paginatedLots.map((lot) => (
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
          <div className="md:hidden">
            {/* Mobile Sort Bar */}
            <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                Trier par
              </label>
              <div className="flex gap-2 overflow-x-auto pb-2">
                {([
                  { field: 'price' as SortField, label: 'Prix' },
                  { field: 'lot_number' as SortField, label: 'N° Lot' },
                  { field: 'title' as SortField, label: 'Titre' },
                  { field: 'status' as SortField, label: 'Statut' },
                  { field: 'depot_location' as SortField, label: 'Lieu' },
                  { field: 'end_date' as SortField, label: 'Date de clôture' }
                ]).map(({ field, label }) => {
                  const isActive = sortField === field
                  return (
                    <button
                      key={field}
                      onClick={() => handleSort(field)}
                      className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                        isActive
                          ? 'bg-primary-600 text-white'
                          : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      {label}
                      {isActive && (sortOrder === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />)}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Mobile Cards */}
            <div className="px-4 py-4 space-y-4">
              {paginatedLots.map((lot) => (
                <LotCard
                  key={lot.id}
                  lot={lot}
                  isFavorite={favorites.has(lot.id)}
                  onToggleFavorite={toggleFavorite}
                />
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3 border-t border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-300 md:flex-row md:items-center md:justify-between">
            <span>
              Page {displayPage} sur {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setDisplayPage(p => Math.max(1, p - 1))}
                disabled={displayPage === 1}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition disabled:cursor-not-allowed disabled:opacity-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                Précédent
              </button>
              <button
                onClick={() => setDisplayPage(p => Math.min(totalPages, p + 1))}
                disabled={displayPage === totalPages}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition disabled:cursor-not-allowed disabled:opacity-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
              >
                Suivant
              </button>
            </div>
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

      {/* Title with Tooltip */}
      <td
        className="px-3 py-2 relative"
        style={{ maxWidth: '450px' }}
      >
        <div
          className="relative inline-block"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <Link
            to={`/lots/${lot.id}`}
            className="text-gray-900 dark:text-white break-words hover:text-primary-600 dark:hover:text-primary-400 transition-colors cursor-pointer"
          >
            {lot.title}
          </Link>

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

      {/* End Date */}
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

function LotCard({
  lot,
  isFavorite,
  onToggleFavorite
}: {
  lot: Lot
  isFavorite: boolean
  onToggleFavorite: (id: number) => void
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span className="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 font-semibold text-primary-700 dark:bg-primary-500/10 dark:text-primary-200">
              Lot #{lot.lot_number}
            </span>
            {lot.status && (
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                {lot.status}
              </span>
            )}
          </div>
          <Link
            to={`/lots/${lot.id}`}
            className="mt-2 block text-base font-semibold text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            {lot.title}
          </Link>
        </div>
        <button
          type="button"
          onClick={() => onToggleFavorite(lot.id)}
          className={`inline-flex h-9 w-9 items-center justify-center rounded-full border transition-colors ${
            isFavorite
              ? 'border-pink-200 bg-pink-50 text-pink-600 dark:border-pink-500/40 dark:bg-pink-500/10 dark:text-pink-200'
              : 'border-gray-200 bg-white text-gray-400 hover:text-pink-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-500'
          }`}
          aria-label={isFavorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}
        >
          <Heart className={`h-5 w-5 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </div>

      {lot.image_url && (
        <div className="mt-4 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
          <img
            src={lot.image_url}
            alt={lot.title}
            className="h-24 w-full object-cover"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      )}

      <div className="mt-4 space-y-2 text-sm text-gray-700 dark:text-gray-300">
        <div className="flex items-center justify-between">
          <span className="text-gray-500 dark:text-gray-400">Prix</span>
          <span className="font-semibold text-gray-900 dark:text-white">
            {lot.price !== null ? `${lot.price.toLocaleString()} €` : 'N/A'}
          </span>
        </div>
        {lot.depot_location && (
          <div>
            <span className="text-gray-500 dark:text-gray-400">Lieu de dépôt</span>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-200">
              {lot.depot_location}
            </p>
          </div>
        )}
        {lot.sale_end_date && (
          <div className="flex items-center justify-between">
            <span className="text-gray-500 dark:text-gray-400">Date de clôture</span>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-200">
              {new Date(lot.sale_end_date).toLocaleDateString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
              })}
            </span>
          </div>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {lot.url && (
          <a
            href={lot.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-primary-200 bg-primary-50 px-3 py-2 text-sm font-medium text-primary-700 transition-colors hover:bg-primary-100 dark:border-primary-500/40 dark:bg-primary-500/10 dark:text-primary-200 dark:hover:bg-primary-500/20"
          >
            <ExternalLink className="h-4 w-4" />
            Voir le lot
          </a>
        )}
        {lot.image_url && (
          <a
            href={lot.image_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Image HD
          </a>
        )}
      </div>
    </div>
  )
}
