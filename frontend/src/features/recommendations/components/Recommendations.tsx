import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { isAxiosError } from 'axios'
import { motion } from 'framer-motion'
import { UtensilsCrossed, Download, Loader2 } from 'lucide-react'
import { GlassCard } from '../../../shared/components'
import { recommendationsService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import NutrientChart from './NutrientChart'
import UserProfileInfo from './UserProfileInfo'
import type { Recommendation } from '../types'
import { humanizeRecommendationClientError } from '../../../shared/utils/apiErrors'

interface RecommendationsProps {
  user: User
  refreshKey?: number
}

interface ApiErrorDetail {
  response?: {
    data?: {
      detail?: unknown
    }
  }
}

const FETCH_DEBOUNCE_MS = 320
const SYNC_POLL_INITIAL_MS = 1000
const SYNC_POLL_MAX_INTERVAL_MS = 8000
const SYNC_POLL_MAX_MS = 45_000

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}

function syncPollDelayMs(attempt: number): number {
  return Math.min(SYNC_POLL_INITIAL_MS * 2 ** attempt, SYNC_POLL_MAX_INTERVAL_MS)
}

function syncMetaIsFresh(meta: {
  user_updated_at: string | null
  latest_rec_created_at: string | null
  labs_fresh_at?: string | null
}) {
  if (!meta.latest_rec_created_at) return false
  const rec = new Date(meta.latest_rec_created_at).getTime()
  const profileT = meta.user_updated_at ? new Date(meta.user_updated_at).getTime() : 0
  const labT = meta.labs_fresh_at ? new Date(meta.labs_fresh_at).getTime() : 0
  const needRefreshIfAfter = Math.max(profileT, labT)
  if (needRefreshIfAfter === 0) return true
  return rec >= needRefreshIfAfter
}

function isHttp404(err: unknown): boolean {
  return isAxiosError(err) && err.response?.status === 404
}

const Recommendations = ({ user, refreshKey }: RecommendationsProps) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(10)
  const [selectedCategory, setSelectedCategory] = useState<'all' | string>('all')
  const [regeneratingAfterProfile, setRegeneratingAfterProfile] = useState(false)
  const [backgroundRefreshNote, setBackgroundRefreshNote] = useState<string | null>(null)
  const latestFetchIdRef = useRef(0)
  const recommendationsRef = useRef<Recommendation[]>([])
  const prevUserValuesRef = useRef({
    diet_type: user.diet_type,
    activity_level: user.activity_level,
    allergies: user.allergies,
    medical_conditions: user.medical_conditions,
    age: user.age,
    sex: user.sex,
    weight: user.weight,
    height: user.height,
  })
  const previousRefreshKeyRef = useRef<number | undefined>(refreshKey)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchRecommendations = useCallback(async (forceRegenerate: boolean = false) => {
    const fetchId = ++latestFetchIdRef.current
    let preloadedFromDb = false
    try {
      if (!user.id) {
        if (fetchId !== latestFetchIdRef.current) return
        setError('ID-ul utilizatorului lipsește. Vă rugăm să vă conectați din nou.')
        setLoading(false)
        setRegeneratingAfterProfile(false)
        return
      }

      setError(null)
      setBackgroundRefreshNote(null)

      let storedPreload: Recommendation[] = []
      try {
        const stored = await recommendationsService.listStored(user.id)
        if (fetchId !== latestFetchIdRef.current) return
        if (Array.isArray(stored) && stored.length > 0) {
          storedPreload = stored as Recommendation[]
          setRecommendations(storedPreload)
          preloadedFromDb = true
          setLoading(false)
        }
      } catch {
        /* listStored e opțional la preload (404 sau rețea — fluxul principal continuă) */
      }

      if (!forceRegenerate && preloadedFromDb) {
        try {
          const meta = await recommendationsService.getSyncMeta(user.id)
          if (fetchId !== latestFetchIdRef.current) return
          const alreadyFresh =
            syncMetaIsFresh(meta) &&
            meta.refresh_status !== 'pending' &&
            meta.refresh_status !== 'failed'
          if (alreadyFresh) {
            setRegeneratingAfterProfile(false)
            setError(null)
            return
          }
        } catch {
          /* continuă cu refresh dacă meta e indisponibil */
        }
        setRegeneratingAfterProfile(true)
      } else if (!preloadedFromDb) {
        setLoading(true)
        setRegeneratingAfterProfile(false)
      } else {
        setRegeneratingAfterProfile(true)
      }

      let data: unknown[]

      try {
        await recommendationsService.startRefreshAsync(user.id, forceRegenerate)
        if (fetchId !== latestFetchIdRef.current) return

        const pollDeadline = Date.now() + SYNC_POLL_MAX_MS
        let pollAttempt = 0
        while (Date.now() < pollDeadline) {
          if (fetchId !== latestFetchIdRef.current) return
          let meta: Awaited<ReturnType<typeof recommendationsService.getSyncMeta>>
          try {
            meta = await recommendationsService.getSyncMeta(user.id)
          } catch (metaErr) {
            if (isHttp404(metaErr)) break
            throw metaErr
          }
          if (fetchId !== latestFetchIdRef.current) return
          if (meta.refresh_status === 'failed') {
            setBackgroundRefreshNote(
              meta.refresh_error?.trim() ||
                'Actualizarea recomandărilor a eșuat. Poți reîncerca din „Încearcă din nou”.'
            )
            break
          }
          if (syncMetaIsFresh(meta) && meta.refresh_status !== 'pending') break
          if (syncMetaIsFresh(meta) && !meta.refresh_status) break
          await sleep(syncPollDelayMs(pollAttempt))
          pollAttempt += 1
        }
        if (Date.now() >= pollDeadline && fetchId === latestFetchIdRef.current) {
          setBackgroundRefreshNote(
            'Procesarea continuă în fundal. Reîmprospătează pagina peste câteva momente dacă lista nu s-a actualizat.'
          )
        }

        try {
          data = (await recommendationsService.listStored(user.id)) as unknown[]
        } catch (listErr) {
          if (isHttp404(listErr)) {
            data = (await recommendationsService.materializeSync(user.id, forceRegenerate)) as unknown[]
          } else {
            throw listErr
          }
        }
      } catch (asyncPathErr) {
        if (isHttp404(asyncPathErr)) {
          data = (await recommendationsService.materializeSync(user.id, forceRegenerate)) as unknown[]
        } else {
          throw asyncPathErr
        }
      }

      if (fetchId !== latestFetchIdRef.current) return
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data as Recommendation[])
        setSelectedCategory('all')
        setVisibleCount(Math.min(10, data.length))
        setError(null)
      } else {
        setError('Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele medicale.')
        setRecommendations([])
      }
    } catch (err: unknown) {
      console.error('Eroare la obținerea recomandărilor:', err)
      let errorMessage = humanizeRecommendationClientError(err)
      const apiError = err as ApiErrorDetail

      if (!errorMessage || errorMessage === 'A apărut o eroare neașteptată') {
        if (err instanceof Error && err.message) {
          errorMessage = humanizeRecommendationClientError(err)
        } else if (apiError?.response?.data?.detail) {
          const detail = apiError.response.data.detail
          if (typeof detail === 'string') {
            errorMessage = detail
          } else if (Array.isArray(detail)) {
            errorMessage = detail
              .map((e) =>
                typeof e === 'object' && e !== null && 'msg' in e
                  ? String((e as { msg?: unknown }).msg ?? JSON.stringify(e))
                  : JSON.stringify(e)
              )
              .join('; ')
          } else if (typeof detail === 'object') {
            const detailObj = detail as { msg?: unknown; message?: unknown }
            errorMessage = String(detailObj.msg || detailObj.message || JSON.stringify(detail))
          }
        }
      }

      if (fetchId !== latestFetchIdRef.current) return
      setError(errorMessage)
      if (!preloadedFromDb) {
        setRecommendations([])
      }
    } finally {
      if (fetchId === latestFetchIdRef.current) {
        setLoading(false)
        setRegeneratingAfterProfile(false)
      }
    }
  }, [user.id])

  useEffect(() => {
    recommendationsRef.current = recommendations
  }, [recommendations])

  useEffect(() => {
    const prevUserValues = prevUserValuesRef.current
    const hasProfileChanged =
      prevUserValues.diet_type !== user.diet_type ||
      prevUserValues.activity_level !== user.activity_level ||
      prevUserValues.allergies !== user.allergies ||
      prevUserValues.medical_conditions !== user.medical_conditions ||
      prevUserValues.age !== user.age ||
      prevUserValues.sex !== user.sex ||
      prevUserValues.weight !== user.weight ||
      prevUserValues.height !== user.height
    const refreshKeyChanged =
      typeof refreshKey === 'number' &&
      refreshKey > 0 &&
      refreshKey !== previousRefreshKeyRef.current

    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    debounceRef.current = setTimeout(() => {
      void fetchRecommendations(false)
    }, FETCH_DEBOUNCE_MS)

    if (hasProfileChanged) {
      prevUserValuesRef.current = {
        diet_type: user.diet_type,
        activity_level: user.activity_level,
        allergies: user.allergies,
        medical_conditions: user.medical_conditions,
        age: user.age,
        sex: user.sex,
        weight: user.weight,
        height: user.height,
      }
    }
    if (refreshKeyChanged) {
      previousRefreshKeyRef.current = refreshKey
      setVisibleCount(10)
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
        debounceRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    user.id,
    user.diet_type,
    user.activity_level,
    user.allergies,
    user.medical_conditions,
    user.age,
    user.sex,
    user.weight,
    user.height,
    user.updated_at,
    refreshKey,
    fetchRecommendations,
  ])

  const exportToPDF = useCallback(() => {
    void import('../pdf/exportRecommendationPdf').then(({ downloadRecommendationPdf }) =>
      downloadRecommendationPdf({
        user: { name: user.name, email: user.email, id: user.id },
        recommendations,
      })
    ).catch((err: unknown) => {
      console.error('Export PDF failed:', err)
    })
  }, [recommendations, user.email, user.id, user.name])

  const userId = user.id
  const categoryCounts = useMemo(
    () =>
      recommendations.reduce<Record<string, number>>((acc, rec) => {
        const category = rec.food?.category || 'Altele'
        acc[category] = (acc[category] || 0) + 1
        return acc
      }, {}),
    [recommendations]
  )
  const availableCategories = useMemo(
    () => Object.keys(categoryCounts).sort((a, b) => (categoryCounts[b] || 0) - (categoryCounts[a] || 0)),
    [categoryCounts]
  )
  const filteredRecommendations = useMemo(
    () =>
      selectedCategory === 'all'
        ? recommendations
        : recommendations.filter((rec) => rec.food?.category === selectedCategory),
    [recommendations, selectedCategory]
  )
  const visibleRecommendations = useMemo(
    () => filteredRecommendations.slice(0, visibleCount),
    [filteredRecommendations, visibleCount]
  )
  const tailCount = visibleRecommendations.length % 3
  const mainCount = tailCount === 0 ? visibleRecommendations.length : visibleRecommendations.length - tailCount
  const mainRecommendations = useMemo(
    () => visibleRecommendations.slice(0, mainCount),
    [visibleRecommendations, mainCount]
  )
  const tailRecommendations = useMemo(
    () => visibleRecommendations.slice(mainCount),
    [visibleRecommendations, mainCount]
  )
  const handleFeedbackSent = useCallback(
    (recId: number, rating: number | null, newLikes: number, newDislikes: number) => {
      setRecommendations((prev) =>
        prev.map((r) =>
          r.recommendation_id === recId
            ? {
                ...r,
                feedback: { ...(r.feedback || { likes: 0, dislikes: 0 }), likes: newLikes, dislikes: newDislikes },
                my_rating: rating,
              }
            : r
        )
      )
    },
    []
  )
  const handleReplaceRequested = useCallback(
    async (recId: number) => {
      const uid = user.id
      if (uid == null) return
      const prev = recommendationsRef.current
      const data = await recommendationsService.replace(uid, recId)
      if (Array.isArray(data) && data.length > 0) {
        const prevById = new Map(prev.map((r) => [r.recommendation_id, r]))
        const merged = (data as Recommendation[]).map((r) => {
          const old = prevById.get(r.recommendation_id)
          if (!old?.explanation) return r
          let reasons = r.explanation?.reasons ?? []
          let tips = r.explanation?.tips
          let patch = false
          const or = old.explanation.reasons?.length ?? 0
          const ot = old.explanation.tips?.length ?? 0
          const nr = reasons.length
          const nt = tips?.length ?? 0
          if (nr === 0 && or > 0) {
            reasons = old.explanation.reasons ?? []
            patch = true
          }
          if (nt === 0 && ot > 0) {
            tips = old.explanation.tips
            patch = true
          }
          if (!patch) return r
          return {
            ...r,
            explanation: {
              ...r.explanation,
              reasons,
              tips,
            },
          }
        })
        setRecommendations(merged)
      } else {
        await fetchRecommendations(false)
      }
    },
    [fetchRecommendations, user.id]
  )

  const showFullPageLoader = loading && recommendations.length === 0
  const showInlineRegenerating = regeneratingAfterProfile && recommendations.length > 0

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <UserProfileInfo user={user} />
      </motion.div>

      {(showInlineRegenerating || backgroundRefreshNote) && (
        <GlassCard className="border border-neonCyan/30 bg-neonCyan/5">
          <div className="flex flex-wrap items-center gap-3 text-slate-200 text-sm">
            {showInlineRegenerating && (
              <Loader2 className="w-5 h-5 text-neonCyan shrink-0 animate-spin" aria-hidden />
            )}
            <p>
              {showInlineRegenerating && (
                <>
                  <span className="font-semibold text-neonCyan">Se actualizează recomandările</span> după
                  modificarea profilului sau analizelor. Poți vedea mai jos lista anterioară până la finalizare.
                </>
              )}
              {backgroundRefreshNote && (
                <span className={showInlineRegenerating ? 'block mt-2 text-slate-300' : ''}>
                  {backgroundRefreshNote}
                </span>
              )}
            </p>
          </div>
        </GlassCard>
      )}

      {recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <GlassCard className="w-full !max-w-none">
            <div className="flex flex-col gap-4 sm:gap-6 mb-6 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-2.5 sm:p-3 rounded-lg shadow-neon flex-shrink-0">
                  <UtensilsCrossed className="w-5 h-5 sm:w-6 sm:h-6 text-black" />
                </div>
                <div className="min-w-0">
                  <h2 className="text-xl sm:text-2xl font-bold text-slate-100">Recomandările tale</h2>
                  <p className="text-slate-400 text-sm">Alimente personalizate pentru nevoile tale nutriționale</p>
                </div>
              </div>
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-5 py-3 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)] whitespace-nowrap touch-manipulation self-start md:self-center"
              >
                <Download className="w-5 h-5 text-neonCyan flex-shrink-0" />
                <span>Exportă PDF</span>
              </motion.button>
            </div>

            <NutrientChart recommendations={recommendations} />
          </GlassCard>
        </motion.div>
      )}

      {recommendations.length > 0 && (
        <GlassCard className="w-full !max-w-none">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-slate-100">Categorii recomandate</h3>
            <p className="text-xs text-slate-400">Poți filtra recomandările pe categorii alimentare.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                setSelectedCategory('all')
                setVisibleCount(10)
              }}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                selectedCategory === 'all'
                  ? 'border-neonCyan bg-neonCyan/20 text-neonCyan'
                  : 'border-slate-600 text-slate-300 hover:border-neonCyan/60'
              }`}
            >
              Toate ({recommendations.length})
            </button>
            {availableCategories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => {
                  setSelectedCategory(category)
                  setVisibleCount(10)
                }}
                className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                  selectedCategory === category
                    ? 'border-neonCyan bg-neonCyan/20 text-neonCyan'
                    : 'border-slate-600 text-slate-300 hover:border-neonCyan/60'
                }`}
              >
                {category} ({categoryCounts[category]})
              </button>
            ))}
          </div>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 items-stretch">
        {mainRecommendations.map((rec, index) => (
          <div key={`${rec.recommendation_id}-${rec.food_id}`} className="w-full flex">
            <RecommendationCard
              recommendation={rec}
              index={index}
              userId={userId}
              onFeedbackSent={handleFeedbackSent}
              onReplaceRequested={handleReplaceRequested}
            />
          </div>
        ))}

        {tailRecommendations.length > 0 && (
          <div className="md:col-span-3 flex justify-center gap-4 sm:gap-6 items-stretch">
            {tailRecommendations.map((rec, idx) => (
              <div key={`${rec.recommendation_id}-${rec.food_id}`} className="w-full md:w-1/3 flex">
                <RecommendationCard
                  recommendation={rec}
                  index={mainRecommendations.length + idx}
                  userId={userId}
                  onFeedbackSent={handleFeedbackSent}
                  onReplaceRequested={handleReplaceRequested}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {filteredRecommendations.length > visibleCount && (
        <div className="flex justify-center mt-8 mb-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setVisibleCount((prev) => Math.min(prev + 5, filteredRecommendations.length))}
            className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center rounded-xl border border-neonCyan/60 bg-gradient-to-r from-slate-800/70 via-slate-900/80 to-slate-950 px-7 py-3 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/70 hover:to-slate-900 hover:border-neonCyan transition-all duration-200 gap-2 shadow-[0_0_18px_rgba(0,245,255,0.35)] hover:shadow-[0_0_30px_rgba(0,245,255,0.6)] touch-manipulation"
          >
            Vezi mai multe
          </motion.button>
        </div>
      )}

      {showFullPageLoader && (
        <GlassCard className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neonCyan mb-4"></div>
          <p className="text-slate-300 text-lg">Se încarcă recomandările...</p>
        </GlassCard>
      )}

      {!loading && error && (
        <GlassCard className="text-center py-12">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <button
            type="button"
            onClick={() => void fetchRecommendations(true)}
            className="min-h-[44px] min-w-[44px] inline-flex items-center justify-center px-4 py-3 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition touch-manipulation"
          >
            Încearcă din nou
          </button>
        </GlassCard>
      )}

      {!loading && !error && recommendations.length === 0 && (
        <GlassCard className="text-center py-12">
          <p className="text-slate-300 text-lg">
            Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele.
          </p>
        </GlassCard>
      )}
    </div>
  )
}

export default Recommendations
