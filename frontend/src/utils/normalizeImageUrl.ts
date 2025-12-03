export function normalizeImageUrl(value: unknown): string | null {
  if (!value) return null

  if (Array.isArray(value)) {
    const firstValid = value.find(
      (entry): entry is string => typeof entry === 'string' && entry.trim().length > 0
    )
    return firstValid ? firstValid.trim() : null
  }

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null

    // Handle serialized JSON strings such as '["https://..."]' or '"https://..."'
    if (trimmed.startsWith('[') || trimmed.startsWith('"')) {
      try {
        return normalizeImageUrl(JSON.parse(trimmed))
      } catch {
        // Fallback to manual cleaning below
      }
    }

    const bracketMatch = trimmed.match(/^\[\s*"?(.+?)"?\s*\]$/)
    if (bracketMatch) {
      return bracketMatch[1]
    }

    return trimmed
  }

  return null
}
