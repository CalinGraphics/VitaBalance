import type { Recommendation } from '../types'

/**
 * Caloriile porției sugerate: `kcal / 100 g` din catalogul validat × porție / 100 (backend-ul trimite deja rezultatul
 * în `facts.kcal_portion`). Returnează `null` când lipsesc datele (ex. rânduri vechi, fără fapte).
 * Strict informativ (bara de obiectiv caloric); nu intră în scorarea recomandărilor.
 */
export function estimatePortionCalories(rec: Pick<Recommendation, 'food' | 'facts'>): number | null {
  const fromFacts = rec.facts?.kcal_portion
  if (typeof fromFacts === 'number' && Number.isFinite(fromFacts)) return Math.round(fromFacts)
  const per100 = Number(rec.food?.calories)
  const portion = Number(rec.facts?.portion?.amount)
  if (!Number.isFinite(per100) || per100 <= 0) return null
  if (!Number.isFinite(portion) || portion <= 0) return null
  return Math.round((per100 * portion) / 100)
}

/** Suma caloriilor estimate pentru o listă de recomandări (cele fără date se ignoră). */
export function sumRecommendationCalories(
  recs: Array<Pick<Recommendation, 'food' | 'facts'>>
): { total: number; counted: number } {
  let total = 0
  let counted = 0
  for (const rec of recs) {
    const kcal = estimatePortionCalories(rec)
    if (kcal != null) {
      total += kcal
      counted += 1
    }
  }
  return { total, counted }
}
