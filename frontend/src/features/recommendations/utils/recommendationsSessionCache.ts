import type { Recommendation } from '../types'

const PREFIX = 'vb-recs-v1-'

function cacheKey(userId: number): string {
  return `${PREFIX}${userId}`
}

export function readRecommendationsSessionCache(userId: number): Recommendation[] | null {
  try {
    const raw = sessionStorage.getItem(cacheKey(userId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed) || parsed.length === 0) return null
    return parsed as Recommendation[]
  } catch {
    return null
  }
}

export function writeRecommendationsSessionCache(
  userId: number,
  recommendations: Recommendation[]
): void {
  if (!recommendations.length) return
  try {
    sessionStorage.setItem(cacheKey(userId), JSON.stringify(recommendations))
  } catch {
    /* quota sau mod privat — ignorăm */
  }
}
