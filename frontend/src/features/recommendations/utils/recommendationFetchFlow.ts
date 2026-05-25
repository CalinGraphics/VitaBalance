import { isAxiosError } from 'axios'
import {
  recommendationsService,
  type RecommendationsSyncMeta,
} from '../../../services/api'

export const SYNC_POLL_INITIAL_MS = 400
export const SYNC_POLL_MAX_INTERVAL_MS = 5000
export const SYNC_POLL_MAX_MS = 120_000

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}

function syncPollDelayMs(attempt: number): number {
  return Math.min(SYNC_POLL_INITIAL_MS * 2 ** attempt, SYNC_POLL_MAX_INTERVAL_MS)
}

export function isHttp404(err: unknown): boolean {
  return isAxiosError(err) && err.response?.status === 404
}

export function syncMetaIsFresh(meta: {
  user_updated_at: string | null
  latest_rec_created_at: string | null
  labs_fresh_at?: string | null
}): boolean {
  if (!meta.latest_rec_created_at) return false
  const rec = new Date(meta.latest_rec_created_at).getTime()
  const profileT = meta.user_updated_at ? new Date(meta.user_updated_at).getTime() : 0
  const labT = meta.labs_fresh_at ? new Date(meta.labs_fresh_at).getTime() : 0
  const needRefreshIfAfter = Math.max(profileT, labT)
  if (needRefreshIfAfter === 0) return true
  return rec >= needRefreshIfAfter
}

/** Nu porni job dacă datele din DB sunt deja la zi (și nu e retry forțat). */
export function shouldSkipBackgroundRefresh(
  meta: RecommendationsSyncMeta,
  forceRegenerate: boolean
): boolean {
  if (forceRegenerate) return false
  return (
    syncMetaIsFresh(meta) &&
    meta.refresh_status !== 'pending' &&
    meta.refresh_status !== 'failed'
  )
}

export function isRefreshPollComplete(
  meta: RecommendationsSyncMeta,
  forceRegenerate: boolean
): boolean {
  if (meta.refresh_status === 'failed') return true
  if (meta.refresh_status === 'done') return true
  if (meta.refresh_status !== 'pending' && syncMetaIsFresh(meta)) return true
  if (!forceRegenerate && syncMetaIsFresh(meta) && meta.refresh_status !== 'pending') {
    return true
  }
  return false
}

export async function pollRecommendationRefresh(
  userId: number,
  options: {
    forceRegenerate: boolean
    isCancelled: () => boolean
    onFailed: (message: string) => void
    onTimeout: () => void
  }
): Promise<'done' | 'failed' | 'timeout' | 'cancelled'> {
  const pollDeadline = Date.now() + SYNC_POLL_MAX_MS
  let pollAttempt = 0

  while (Date.now() < pollDeadline) {
    if (options.isCancelled()) return 'cancelled'

    let meta: RecommendationsSyncMeta
    try {
      meta = await recommendationsService.getSyncMeta(userId)
    } catch (metaErr) {
      if (isHttp404(metaErr)) return 'done'
      throw metaErr
    }

    if (options.isCancelled()) return 'cancelled'

    if (meta.refresh_status === 'failed') {
      options.onFailed(
        meta.refresh_error?.trim() ||
          'Actualizarea recomandărilor a eșuat. Lista anterioară rămâne afișată.'
      )
      return 'failed'
    }

    if (isRefreshPollComplete(meta, options.forceRegenerate)) {
      return 'done'
    }

    await sleep(syncPollDelayMs(pollAttempt))
    pollAttempt += 1
  }

  if (!options.isCancelled()) {
    options.onTimeout()
  }
  return 'timeout'
}

export async function loadStoredRecommendations(userId: number): Promise<unknown[]> {
  return (await recommendationsService.listStored(userId)) as unknown[]
}

/**
 * Pornește refresh async, așteaptă finalizarea (poll), returnează lista din DB.
 * Fallback sync doar dacă endpoint-urile async lipsesc (404).
 */
export async function runRecommendationRefreshPipeline(
  userId: number,
  forceRegenerate: boolean,
  isCancelled: () => boolean,
  callbacks: {
    onFailedNote: (message: string) => void
    onTimeoutNote: () => void
  }
): Promise<unknown[]> {
  try {
    await recommendationsService.startRefreshAsync(userId, forceRegenerate)
  } catch (asyncErr) {
    if (!isHttp404(asyncErr)) throw asyncErr
    return recommendationsService.materializeSync(userId, forceRegenerate)
  }

  if (isCancelled()) return []

  await pollRecommendationRefresh(userId, {
    forceRegenerate,
    isCancelled,
    onFailed: callbacks.onFailedNote,
    onTimeout: callbacks.onTimeoutNote,
  })

  if (isCancelled()) return []

  try {
    return await loadStoredRecommendations(userId)
  } catch (listErr) {
    if (!isHttp404(listErr)) throw listErr
    return recommendationsService.materializeSync(userId, forceRegenerate)
  }
}

/** Pornește refresh async fără a bloca UI-ul (folosit după ce lista e deja afișată). */
export async function startRecommendationRefreshJob(
  userId: number,
  forceRegenerate: boolean
): Promise<void> {
  try {
    await recommendationsService.startRefreshAsync(userId, forceRegenerate)
  } catch (asyncErr) {
    if (!isHttp404(asyncErr)) throw asyncErr
    await recommendationsService.materializeSync(userId, forceRegenerate)
  }
}
