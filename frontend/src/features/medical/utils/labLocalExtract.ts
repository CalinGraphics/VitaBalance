/**
 * Parsare locală (regex) a valorilor de laborator din textul extras din PDF.
 * Complementară față de endpoint-ul backend; rulează în paralel pentru acoperire mai bună.
 */

export type LabKey =
  | 'hemoglobin'
  | 'ferritin'
  | 'vitamin_d'
  | 'vitamin_b12'
  | 'calcium'
  | 'magnesium'
  | 'zinc'
  | 'protein'
  | 'folate'
  | 'vitamin_a'
  | 'iodine'
  | 'vitamin_k'
  | 'potassium'

export const LAB_KEYS: LabKey[] = [
  'hemoglobin',
  'ferritin',
  'vitamin_d',
  'vitamin_b12',
  'calcium',
  'magnesium',
  'zinc',
  'protein',
  'folate',
  'vitamin_a',
  'iodine',
  'vitamin_k',
  'potassium',
]

/** Normalizare pentru potrivire text (observații / note, același algoritm ca la parsarea PDF). */
export function normalizeLabNoteText(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

export function extractLabValuesFromTextLocal(text: string): Partial<Record<LabKey, number>> {
  const raw = text || ''
  const t = raw
    .replace(/\u00a0/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  const normalized = normalizeLabNoteText(raw)
  const normalizedFlat = normalized.replace(/\s+/g, ' ').trim()
  const normalizedLines = raw
    .split(/\r?\n/)
    .map((ln) => normalizeLabNoteText(ln))
    .filter(Boolean)

  const tryParse = (rawToken: string | undefined): number | undefined => {
    if (!rawToken) return undefined
    const n = Number(rawToken.replace(',', '.'))
    return Number.isFinite(n) ? n : undefined
  }

  const pickFirst = (patterns: RegExp[], sources: string[] = [t, normalizedFlat]): number | undefined => {
    for (const p of patterns) {
      for (const source of sources) {
        const m = source.match(p)
        if (m?.[1]) {
          const v = tryParse(m[1])
          if (v !== undefined) return v
        }
      }
    }
    return undefined
  }

  const pickLineValue = (
    lineKeyPatterns: RegExp[],
    isPlausible?: (value: number) => boolean
  ): number | undefined => {
    for (const line of normalizedLines) {
      let startIndex = -1
      for (const kp of lineKeyPatterns) {
        const m = kp.exec(line)
        if (m && m.index >= 0 && (startIndex === -1 || m.index < startIndex)) {
          startIndex = m.index
        }
      }
      if (startIndex < 0) continue

      for (const m of line.matchAll(/\d+(?:[.,]\d+)?/g)) {
        if ((m.index ?? -1) < startIndex) continue
        const token = m[0]
        const nextChunk = line.slice((m.index ?? 0) + token.length, (m.index ?? 0) + token.length + 8)
        if (/^\s*[-–]\s*\d/.test(nextChunk)) continue
        const v = tryParse(token)
        if (v !== undefined && (!isPlausible || isPlausible(v))) return v
      }
    }
    return undefined
  }

  return {
    hemoglobin:
      pickFirst([
        /\b(?:hemoglobina|hemoglobină|hemoglobin)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
        /\b(?:hgb)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
        /\b(?:hb)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      ]) ??
      pickLineValue([/\bhemoglobina\b/i, /\bhemoglobin\b/i, /\bhgb\b/i, /\bhb\b/i], (v) => v >= 3 && v <= 25),
    ferritin: pickFirst([
      /\b(?:feritina|feritină|ferritin)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\b(?:feritina|ferritina)\s+seric[ăa]?\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    vitamin_d: pickFirst([
      /\b(?:25\s*-?\s*oh\s*-?\s*d|25\s*\(?oh\)?\s*d|vit(?:\.)?\s*d|vitamina\s*d)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    vitamin_b12: pickFirst([
      /\b(?:vit(?:\.)?\s*b\s*12|vitamina\s*b\s*12|b\s*12|cobalamina|cianocobalamina)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    calcium: pickFirst([
      /\b(?:calciu|calcium)\b(?:\s+(?:total|ionic|seric|serica))?\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\bca\b\s*[:=]\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    magnesium: pickFirst([
      /\b(?:magneziu|magnesium)\b(?:\s+seric)?\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\bmg\b\s*[:=]\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    zinc: pickFirst([/\b(?:zinc|zn)\b(?:\s+seric)?\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    protein: pickFirst([
      /\b(?:proteine|proteine\s+totale|proteine\s+serice|protein(?:a)?)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    folate: pickFirst([
      /\b(?:folat|folate|acid\s*folic|folic\s*acid|vit(?:\.)?\s*b9|vitamina\s*b9)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    vitamin_a: pickFirst([/\b(?:vit(?:\.)?\s*a|vitamina\s*a|retinol)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    iodine: pickFirst([/\b(?:iod|iodine|iodina)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    vitamin_k: pickFirst([
      /\b(?:vit(?:\.)?\s*k|vitamina\s*k|phylloquinone|filochinona)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    potassium: pickFirst([
      /\b(?:potasiu|potassium)\b(?:\s+seric)?\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\bk\b\s*[:=]\s*(\d+(?:[.,]\d+)?)/i,
    ]),
  }
}

export type LabExtractApiScalar = number | string | null | undefined

export type LabExtractFromApi = Partial<Record<LabKey, LabExtractApiScalar>>

export function coerceLabNumeric(value: LabExtractApiScalar): number | undefined {
  if (value === null || value === undefined || value === '') return undefined
  if (typeof value === 'number') return Number.isFinite(value) ? value : undefined
  if (typeof value === 'string') {
    const n = Number(value.replace(',', '.'))
    return Number.isFinite(n) ? n : undefined
  }
  return undefined
}
