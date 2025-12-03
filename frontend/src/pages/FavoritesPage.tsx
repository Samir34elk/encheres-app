import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Heart, Search, Trash2, ExternalLink, TrendingDown, Tag, FileText } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'
import { normalizeImageUrl } from '../utils/normalizeImageUrl'

interface Favorite {
  id: number
  lot_id: number
  lot_number: number
  lot_title: string
  lot_price: number | null
  lot_image_url: string | null
  lot_url: string | null
  lot_status: string | null
  notes: string | null
  tags: string[] | null
  created_at: string
  price_changed: boolean
}

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<Favorite[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedTag, setSelectedTag] = useState<string>('')
  const [editingNotes, setEditingNotes] = useState<number | null>(null)
  const [editingTags, setEditingTags] = useState<number | null>(null)
  const [notesText, setNotesText] = useState('')
  const [tagsText, setTagsText] = useState('')

  useEffect(() => {
    fetchFavorites()
  }, [])

  const fetchFavorites = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/favorites')
      const items: Favorite[] = (data?.items || []).map((item: Favorite) => ({
        ...item,
        lot_image_url: normalizeImageUrl(item.lot_image_url)
      }))
      setFavorites(items)
    } catch (error) {
      console.error('Failed to fetch favorites:', error)
      toast.error('Erreur lors du chargement des favoris')
    } finally {
      setLoading(false)
    }
  }

  const removeFavorite = async (lotId: number) => {
    try {
      await api.delete(`/favorites/${lotId}`)
      setFavorites(favorites.filter(f => f.lot_id !== lotId))

      // Update localStorage
      const stored = localStorage.getItem('auctionFavorites')
      if (stored) {
        const favSet = new Set(JSON.parse(stored))
        favSet.delete(lotId)
        localStorage.setItem('auctionFavorites', JSON.stringify(Array.from(favSet)))
      }

      toast.success('Favori supprimé')
    } catch (error) {
      console.error('Failed to remove favorite:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  const updateNotes = async (favoriteId: number) => {
    try {
      await api.patch(`/favorites/${favoriteId}`, { notes: notesText || null })
      setFavorites(favorites.map(f =>
        f.id === favoriteId ? { ...f, notes: notesText || null } : f
      ))
      setEditingNotes(null)
      toast.success('Notes mises à jour')
    } catch (error) {
      console.error('Failed to update notes:', error)
      toast.error('Erreur lors de la mise à jour')
    }
  }

  const updateTags = async (favoriteId: number) => {
    try {
      const tags = tagsText.split(',').map(t => t.trim()).filter(Boolean)
      await api.patch(`/favorites/${favoriteId}`, { tags: tags.length > 0 ? tags : null })
      setFavorites(favorites.map(f =>
        f.id === favoriteId ? { ...f, tags: tags.length > 0 ? tags : null } : f
      ))
      setEditingTags(null)
      toast.success('Tags mis à jour')
    } catch (error) {
      console.error('Failed to update tags:', error)
      toast.error('Erreur lors de la mise à jour')
    }
  }

  // Get all unique tags
  const allTags = Array.from(
    new Set(favorites.flatMap(f => f.tags || []))
  ).sort()

  // Filter favorites
  const filteredFavorites = favorites.filter(fav => {
    if (searchTerm) {
      const search = searchTerm.toLowerCase()
      if (!fav.lot_title.toLowerCase().includes(search) &&
          !fav.lot_number.toString().includes(search)) {
        return false
      }
    }

    if (selectedTag && (!fav.tags || !fav.tags.includes(selectedTag))) {
      return false
    }

    return true
  })

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Mes Favoris
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {filteredFavorites.length} favori{filteredFavorites.length > 1 ? 's' : ''}
            {filteredFavorites.length !== favorites.length && ` sur ${favorites.length}`}
          </p>
        </div>
      </div>

      {/* Filters */}
      {favorites.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Rechercher un favori..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Tag filter */}
            {allTags.length > 0 && (
              <select
                value={selectedTag}
                onChange={(e) => setSelectedTag(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Tous les tags</option>
                {allTags.map(tag => (
                  <option key={tag} value={tag}>{tag}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      )}

      {/* Favorites List */}
      {filteredFavorites.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {favorites.length === 0 ? 'Aucun favori' : 'Aucun résultat'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {favorites.length === 0
              ? 'Ajoutez des lots à vos favoris pour les suivre facilement'
              : 'Essayez de modifier vos filtres'}
          </p>
          {favorites.length === 0 && (
            <Link
              to="/lots"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Parcourir les lots
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredFavorites.map((fav) => (
            <div
              key={fav.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex gap-6">
                  {/* Image */}
                  <div className="flex-shrink-0">
                    {fav.lot_image_url ? (
                      <img
                        src={fav.lot_image_url}
                        alt={fav.lot_title}
                        className="w-32 h-32 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-32 h-32 bg-gray-200 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                        <Heart className="w-8 h-8 text-gray-400" />
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <Link
                          to={`/lots/${fav.lot_id}`}
                          className="text-xl font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {fav.lot_title}
                        </Link>
                        <div className="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
                          <span>Lot #{fav.lot_number}</span>
                          {fav.lot_status && (
                            <>
                              <span>•</span>
                              <span>{fav.lot_status}</span>
                            </>
                          )}
                          {fav.price_changed && (
                            <>
                              <span>•</span>
                              <span className="flex items-center gap-1 text-green-600 dark:text-green-400 font-medium">
                                <TrendingDown className="w-3 h-3" />
                                Prix modifié
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Price */}
                      <div className="text-right ml-4">
                        {fav.lot_price !== null ? (
                          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {fav.lot_price.toLocaleString()} €
                          </div>
                        ) : (
                          <div className="text-sm text-gray-400">Prix non disponible</div>
                        )}
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="mb-3">
                      {editingTags === fav.id ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={tagsText}
                            onChange={(e) => setTagsText(e.target.value)}
                            placeholder="tag1, tag2, tag3..."
                            className="flex-1 px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                            autoFocus
                          />
                          <button
                            onClick={() => updateTags(fav.id)}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            Sauver
                          </button>
                          <button
                            onClick={() => setEditingTags(null)}
                            className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm hover:bg-gray-300 dark:hover:bg-gray-600"
                          >
                            Annuler
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 flex-wrap">
                          {fav.tags && fav.tags.length > 0 ? (
                            fav.tags.map((tag, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs rounded-full"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-gray-400 italic">Aucun tag</span>
                          )}
                          <button
                            onClick={() => {
                              setEditingTags(fav.id)
                              setTagsText(fav.tags?.join(', ') || '')
                            }}
                            className="text-blue-600 dark:text-blue-400 hover:underline text-xs flex items-center gap-1"
                          >
                            <Tag className="w-3 h-3" />
                            Modifier
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Notes */}
                    <div>
                      {editingNotes === fav.id ? (
                        <div className="space-y-2">
                          <textarea
                            value={notesText}
                            onChange={(e) => setNotesText(e.target.value)}
                            placeholder="Ajoutez vos notes personnelles..."
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                            autoFocus
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => updateNotes(fav.id)}
                              className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                            >
                              Sauver
                            </button>
                            <button
                              onClick={() => setEditingNotes(null)}
                              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-sm hover:bg-gray-300 dark:hover:bg-gray-600"
                            >
                              Annuler
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-start gap-2">
                          <FileText className="w-4 h-4 text-gray-400 mt-1" />
                          <div className="flex-1">
                            {fav.notes ? (
                              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                                {fav.notes}
                              </p>
                            ) : (
                              <p className="text-sm text-gray-400 italic">Aucune note</p>
                            )}
                            <button
                              onClick={() => {
                                setEditingNotes(fav.id)
                                setNotesText(fav.notes || '')
                              }}
                              className="text-blue-600 dark:text-blue-400 hover:underline text-xs mt-1"
                            >
                              {fav.notes ? 'Modifier' : 'Ajouter une note'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Link
                    to={`/lots/${fav.lot_id}`}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                  >
                    Voir les détails
                  </Link>

                  {fav.lot_url && (
                    <a
                      href={fav.lot_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Voir sur le site
                    </a>
                  )}

                  <button
                    onClick={() => removeFavorite(fav.lot_id)}
                    className="ml-auto flex items-center gap-2 px-4 py-2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    Supprimer
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
