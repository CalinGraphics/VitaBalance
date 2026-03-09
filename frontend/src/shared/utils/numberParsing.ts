export function sanitizeIntInput(raw: string): string {
  return raw.replace(/[^\d]/g, '')
}

export function sanitizeDecimalInput(raw: string): string {
  // Allow digits plus "," and "."; remove spaces and other chars.
  let s = raw.replace(/[^\d.,\s]/g, '')
  s = s.replace(/\s+/g, '')

  // Keep only first decimal separator.
  const firstSepIdx = s.search(/[.,]/)
  if (firstSepIdx >= 0) {
    const sep = s[firstSepIdx]
    const before = s.slice(0, firstSepIdx)
    const after = s
      .slice(firstSepIdx + 1)
      .replace(/[.,]/g, '') // drop additional separators
    s = `${before}${sep}${after}`
  }

  return s
}

export function parseOptionalInt(raw: string): number | undefined {
  const s = raw.trim()
  if (!s) return undefined
  const n = Number.parseInt(s, 10)
  return Number.isFinite(n) ? n : undefined
}

export function parseOptionalDecimal(raw: string): number | undefined {
  const s = raw.trim()
  if (!s) return undefined
  const normalized = s.replace(',', '.')
  const n = Number(normalized)
  return Number.isFinite(n) ? n : undefined
}

