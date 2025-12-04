const API_BASE = (import.meta as any).env?.VITE_API_URL?.replace(/\/+$/, '') || ''
const IMAGE_PROXY_BASE = ((import.meta as any).env?.VITE_IMAGE_PROXY_URL as string | undefined)?.replace(/\/+$/, '')
  || (API_BASE ? `${API_BASE}/media` : '')
const REMOTE_IMAGE_BASE = 'https://encheres-domaine.gouv.fr/admin/media/catalog/product/'

function toStringList(value: unknown): string[] {
  if (!value) return []

  if (Array.isArray(value)) {
    return value
      .flatMap((entry) => toStringList(entry))
      .filter((entry): entry is string => typeof entry === 'string' && entry.trim().length > 0)
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return []

    // Handle serialized JSON strings such as '["path1", "path2"]' or '"path"'
    if (trimmed.startsWith('[') || trimmed.startsWith('{') || trimmed.startsWith('"')) {
      try {
        return toStringList(JSON.parse(trimmed))
      } catch {
        // Ignore parsing errors and fallback to manual cleaning
      }
    }

    const bracketMatch = trimmed.match(/^\[\s*"?(.+?)"?\s*\]$/)
    if (bracketMatch) {
      return [bracketMatch[1]]
    }

    return [trimmed]
  }

  return []
}

function buildFullUrl(raw: string): string | null {
  const cleaned = raw.trim()
  if (!cleaned) return null

  if (/^https?:\/\//i.test(cleaned)) {
    try {
      const url = new URL(cleaned)
      const path = url.pathname.replace(/^\/+/, '')
      // If the URL already points to the official media host, rewrite through proxy when available
      if (IMAGE_PROXY_BASE && /encheres-domaine\.(gouv\.fr|com)/i.test(url.hostname)) {
        return `${IMAGE_PROXY_BASE}/${path}`
      }
      return cleaned
    } catch {
      return cleaned
    }
  }

  const normalizedKey = cleaned.replace(/^\/+/, '')
  const base = IMAGE_PROXY_BASE || REMOTE_IMAGE_BASE
  return `${base.replace(/\/+$/, '')}/${normalizedKey}`
}

export function normalizeImageUrls(value: unknown): string[] {
  const urls = toStringList(value)
    .map(buildFullUrl)
    .filter((entry): entry is string => Boolean(entry))

  const unique = Array.from(new Set(urls))
  return unique
}

export function normalizeImageUrl(value: unknown): string | null {
  const urls = normalizeImageUrls(value)
  return urls[0] ?? null
}
