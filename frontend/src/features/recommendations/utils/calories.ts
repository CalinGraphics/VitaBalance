import type { Recommendation } from '../types'

/**
 * Estimare orientativă a caloriilor porției sugerate: `kcal / 100 g` din catalogul de alimente × porție / 100.
 * Mililitrii sunt tratați ca grame (aproximare acceptabilă pentru băuturi). Returnează `null` când lipsesc datele.
 * Este strict informativ (bara de obiectiv caloric) și nu intră în scorarea recomandărilor.
 */
export function estimatePortionCalories(
  rec: Pick<Recommendation, 'food' | 'explanation'>
): number | null {
  const per100 = Number(rec.food?.calories)
  const portion = Number(rec.explanation?.portion)
  if (!Number.isFinite(per100) || per100 <= 0) return null
  if (!Number.isFinite(portion) || portion <= 0) return null
  return Math.round((per100 * portion) / 100)
}

/** Suma caloriilor estimate pentru o listă de recomandări (cele fără date se ignoră). */
export function sumRecommendationCalories(
  recs: Array<Pick<Recommendation, 'food' | 'explanation'>>
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
