/**
 * Types centralisés pour l'application
 */

export interface Lot {
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
  // Nouveaux champs GraphQL
  categories: string[] | null
  caracteristiques: Record<string, any> | null
  professionnel: boolean
  price_reserve: number | null
}

export interface LotWithFavorite extends Lot {
  is_favorited: boolean
  user_tags: string | null
  user_notes: string | null
}

export interface Sale {
  id: number
  sale_number: string
  title: string
  description: string | null
  organiser: string
  type_vente: string | null
  total_lots: number | null
  start_date: string | null
  end_date: string | null
  status: string | null
  image_url: string | null
  professional_only: boolean
  categories: string[] | null
  first_seen: string
  last_updated: string
  is_active: number
}

export interface PriceHistory {
  id: number
  price: number
  status: string | null
  recorded_at: string
}

export interface Alert {
  id: number
  lot_id: number
  alert_type: 'price_drop' | 'price_below' | 'any_change'
  target_price: number | null
  is_active: boolean
  created_at: string
  last_notified_at: string | null
  lot?: Lot
}

export interface Favorite {
  lot_id: number
  tags: string | null
  notes: string | null
  created_at: string
  lot?: Lot
}

export interface Notification {
  id: number
  title: string
  message: string
  type: string
  is_read: boolean
  created_at: string
  lot_id: number | null
  lot?: Lot
}
