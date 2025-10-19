export interface SaleMetadata {
  organizer?: string
  saleType?: string
  tags: string[]
  statusLabel?: string
  raw?: string
}

const sanitizeString = (value?: unknown) =>
  typeof value === 'string' ? value.trim() : undefined

export function parseSaleMetadata(raw?: string | null): SaleMetadata {
  const base: SaleMetadata = {
    organizer: undefined,
    saleType: undefined,
    tags: [],
    statusLabel: undefined,
    raw: raw?.trim() || undefined
  }

  if (!raw || raw.trim().length === 0) {
    return base
  }

  try {
    const parsed = JSON.parse(raw)
    const organizer = sanitizeString(parsed.organizer ?? parsed.location)
    const saleType = sanitizeString(parsed.sale_type ?? parsed.saleType)
    const statusLabel = sanitizeString(parsed.status_label ?? parsed.statusLabel)
    const tags = Array.isArray(parsed.tags)
      ? parsed.tags
          .filter((tag: unknown): tag is string => typeof tag === 'string' && tag.trim().length > 0)
          .map((tag: string) => tag.trim())
      : []

    return {
      organizer,
      saleType,
      statusLabel,
      tags,
      raw: raw.trim()
    }
  } catch {
    const trimmed = raw.trim()
    const organizerMatch = trimmed.match(/organisateur\s*[:\-–]\s*(.+)/i)

    if (organizerMatch?.[1]) {
      const organizerValue = organizerMatch[1].trim()
      return {
        organizer: organizerValue,
        saleType: undefined,
        statusLabel: undefined,
        tags: [],
        raw: trimmed
      }
    }

    const looksLikeSaleType = /^vente|^appel d'offre/i.test(trimmed)
    return {
      organizer: looksLikeSaleType ? undefined : trimmed,
      saleType: looksLikeSaleType ? trimmed : undefined,
      statusLabel: undefined,
      tags: [],
      raw: trimmed
    }
  }
}
