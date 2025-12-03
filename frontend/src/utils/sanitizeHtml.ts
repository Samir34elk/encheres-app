// Minimal HTML sanitizer for descriptions
export function sanitizeHtml(input: string | null | undefined): string {
  if (!input) return ''

  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(input, 'text/html')

    // Remove dangerous nodes
    doc.querySelectorAll('script, style').forEach((el) => el.remove())

    // Strip event handlers and javascript: URLs
    doc.querySelectorAll<HTMLElement>('*').forEach((el) => {
      Array.from(el.attributes).forEach((attr) => {
        const name = attr.name.toLowerCase()
        const value = attr.value.trim().toLowerCase()
        if (name.startsWith('on')) {
          el.removeAttribute(attr.name)
        }
        if ((name === 'href' || name === 'src') && value.startsWith('javascript:')) {
          el.removeAttribute(attr.name)
        }
      })
    })

    return doc.body.innerHTML.trim()
  } catch {
    return ''
  }
}

export function extractTextFromHtml(input: string | null | undefined): string {
  if (!input) return ''
  try {
    const parser = new DOMParser()
    const doc = parser.parseFromString(input, 'text/html')
    return doc.body.textContent?.trim() || ''
  } catch {
    return input.replace(/<[^>]*>/g, '').trim()
  }
}
