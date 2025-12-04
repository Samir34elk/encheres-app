const API_BASE = (import.meta as any).env?.VITE_API_URL?.replace(/\/+$/, '') || ''
// Use Python proxy for image serving and caching
const IMAGE_BASE = API_BASE + '/media'

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

      // If from encheres-domaine, try local cache first
      if (/encheres-domaine\.(gouv\.fr|com)/i.test(url.hostname)) {
        const path = url.pathname.replace(/^\/+/, '')
        const cleanPath = path.replace(/^admin\/media\/catalog\/product\//, '')
        return `${IMAGE_BASE}/${cleanPath}`
      }

      return cleaned
    } catch {
      return cleaned
    }
  }

  // Relative path - clean and use local cache
  let cleanPath = cleaned.replace(/^\/+/, '')

  // Remove duplicate base path if present
  const duplicatePrefix = 'admin/media/catalog/product/'
  if (cleanPath.startsWith(duplicatePrefix)) {
    cleanPath = cleanPath.substring(duplicatePrefix.length)
  }

  return `${IMAGE_BASE}/${cleanPath}`
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
