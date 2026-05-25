import { recommendationsService } from '../../../services/api'
import type { Recommendation } from '../types'
import { writeRecommendationsSessionCache } from './recommendationsSessionCache'

/**
 * Regenerare sincronă după salvare profil/analize — lista e gata înainte de navigare.
 */
export async function regenerateRecommendationsAfterSave(
  userId: number
): Promise<Recommendation[]> {
  const data = (await recommendationsService.materializeSync(userId, true)) as unknown[]
  const list = Array.isArray(data) ? (data as Recommendation[]) : []
  if (list.length > 0) {
    writeRecommendationsSessionCache(userId, list)
  }
  return list
}
