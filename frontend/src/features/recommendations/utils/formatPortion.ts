function isDrinkCategory(category?: string | null): boolean {
  if (!category) return false
  const n = category
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
  return n.includes('bauturi')
}

/** Afișare porție sugerată (g sau ml) din payload API. */
export function formatPortionSuggestion(
  portion: number | undefined | null,
  unit?: string | null,
  foodCategory?: string | null
): string {
  const amount = Math.round(Number(portion) || 0)
  if (amount <= 0) return '—'
  let u = (unit || '').toLowerCase().trim()
  if (!u && isDrinkCategory(foodCategory)) u = 'ml'
  if (!u) u = 'g'
  if (u === 'ml') return `${amount} ml`
  return `${amount} g`
}
