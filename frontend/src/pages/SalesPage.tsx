import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import axios from 'axios'
import { CalendarDays, Clock, Package, ExternalLink, MapPin } from 'lucide-react'
import { parseSaleMetadata } from '../utils/saleMetadata'
import { normalizeImageUrls } from '../utils/normalizeImageUrl'

interface Sale {
  id: number
  sale_number: number
  title: string
  description: string | null
  status: string
  total_lots: number
  is_scraped: boolean
  created_at: string
  updated_at: string
  start_date?: string | null
  end_date?: string | null
  url?: string | null
  image_url?: string | null
  image_urls?: string[] | null
}

export default function SalesPage() {
  const [sales, setSales] = useState<Sale[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    fetchSales()
  }, [page])

  const getComparableDate = (sale: Sale) => {
    const candidates = [sale.end_date, sale.start_date, sale.created_at, sale.updated_at]
    for (const candidate of candidates) {
      if (!candidate) continue
      const parsed = new Date(candidate)
      if (!Number.isNaN(parsed.getTime())) {
        return parsed.getTime()
      }
    }
    return Number.POSITIVE_INFINITY
  }

  const normalizeSales = (items: Sale[]) =>
    items
      .filter(sale => sale.status !== 'cancelled')
      .sort((a, b) => getComparableDate(a) - getComparableDate(b))

  const fetchSales = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/sales`, {
        params: { page, size: 20 }
      })
      const items: Sale[] = (response.data.items || []).map((sale: any) => {
        const image_urls = normalizeImageUrls(sale.image_urls ?? sale.image_url)
        return {
          ...sale,
          image_urls,
          image_url: image_urls[0] ?? sale.image_url ?? null
        }
      })

      const normalized = normalizeSales(items)
      setSales(normalized)
      setTotalPages(response.data.pages)
    } catch (error) {
      toast.error('Erreur lors du chargement des ventes')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (value?: string | null) => {
    if (!value) return null
    const parsed = new Date(value)
    if (Number.isNaN(parsed.getTime())) return null
    return `${parsed.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })} · ${parsed.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })}`
  }

  if (loading && sales.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Ventes aux Enchères
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-3xl">
          Parcourez l&apos;ensemble des ventes en cours ou programmées et accédez aux lots détaillés en un clic.
        </p>
      </div>

      {sales.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Aucune vente disponible</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sales.map((sale) => {
              const metadata = parseSaleMetadata(sale.description)
              const startDate = formatDateTime(sale.start_date)
              const endDate = formatDateTime(sale.end_date)
              const status = sale.status
              const statusLabel =
                status === 'active' ? 'Enchères en cours' : status === 'closed' ? 'Vente clôturée' : 'Vente à venir'
              const statusBadge =
                status === 'active'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : status === 'closed'
                    ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'

              return (
                <Link
                  key={sale.id}
                  to={`/sales/${sale.sale_number}`}
                  className="group flex h-full flex-col justify-between rounded-2xl border border-gray-200/80 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:border-primary-200 hover:shadow-xl dark:border-gray-700 dark:bg-gray-800 dark:hover:border-primary-500/40"
                >
                  <div className="space-y-5">
                    {sale.image_url && (
                      <div className="overflow-hidden rounded-xl border border-gray-100 shadow-sm dark:border-gray-700">
                        <img
                          src={sale.image_url}
                          alt={sale.title}
                          className="h-40 w-full object-cover transition-transform duration-300 group-hover:scale-105"
                          loading="lazy"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                          }}
                        />
                      </div>
                    )}

                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-3">
                        {metadata.saleType && (
                          <span className="inline-flex items-center rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary-600 dark:bg-primary-500/10 dark:text-primary-200">
                            {metadata.saleType}
                          </span>
                        )}
                        <h2 className="text-xl font-semibold text-gray-900 transition-colors group-hover:text-primary-700 dark:text-white dark:group-hover:text-primary-200">
                          {sale.title}
                        </h2>
                        {metadata.organizer && (
                          <p className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                            <MapPin className="h-4 w-4 text-primary-500 dark:text-primary-300" />
                            <span>
                              Organisateur&nbsp;:
                              <span className="ml-1 font-medium text-gray-900 dark:text-gray-100">
                                {metadata.organizer}
                              </span>
                            </span>
                          </p>
                        )}
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusBadge}`}>
                        {statusLabel}
                      </span>
                    </div>

                    {metadata.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {metadata.tags.slice(0, 4).map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center rounded-full border border-primary-100 bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700 dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-200"
                          >
                            {tag}
                          </span>
                        ))}
                        {metadata.tags.length > 4 && (
                          <span className="inline-flex items-center rounded-full border border-gray-200 bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
                            +{metadata.tags.length - 4}
                          </span>
                        )}
                      </div>
                    )}

                    <div className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
                      <div className="flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-3 py-3 dark:border-gray-700 dark:bg-gray-800/70">
                        <Package className="h-5 w-5 text-primary-600 dark:text-primary-300" />
                        <div>
                          <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                            Lots disponibles
                          </p>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {sale.total_lots} lot{sale.total_lots > 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>

                      {startDate && (
                        <div className="flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-3 py-3 dark:border-gray-700 dark:bg-gray-800/70">
                          <CalendarDays className="h-5 w-5 text-primary-600 dark:text-primary-300" />
                          <div>
                            <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                              Début des enchères
                            </p>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {startDate}
                            </p>
                          </div>
                        </div>
                      )}

                      {endDate && (
                        <div className="flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-3 py-3 dark:border-gray-700 dark:bg-gray-800/70">
                          <Clock className="h-5 w-5 text-primary-600 dark:text-primary-300" />
                          <div>
                            <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">
                              {status === 'closed' ? 'Vente clôturée' : 'Clôture prévue'}
                            </p>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {endDate}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4 text-sm dark:border-gray-700">
                    {sale.url ? (
                      <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                        <ExternalLink className="h-4 w-4" />
                        <span>Lien officiel disponible</span>
                      </div>
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400">
                        Accédez au détail des lots
                      </span>
                    )}
                    <span className="inline-flex items-center gap-1 font-medium text-primary-600 transition-colors group-hover:text-primary-700 dark:text-primary-300 dark:group-hover:text-primary-200">
                      Consulter la vente
                      <ExternalLink className="h-4 w-4" />
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex justify-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Précédent
              </button>
              <span className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg">
                Page {page} sur {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Suivant
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
