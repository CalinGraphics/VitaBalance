import { lazy, Suspense, useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { BarChart3, Filter } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, Spinner } from '../../../shared/components'
import i18n, { currentLanguage } from '../../../shared/i18n'
import { recommendationsService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import RecommendationSkeleton, { ChartSkeleton } from './RecommendationSkeleton'

// Graficul (recharts) e greu: se încarcă separat, după ce cardurile sunt deja pe ecran.
const NutrientChart = lazy(() => import('./NutrientChart'))
import RecommendationsHero from './RecommendationsHero'
import CaloricGoalProgress from './CaloricGoalProgress'
import type { Recommendation } from '../types'
import { humanizeRecommendationClientError } from '../../../shared/utils/apiErrors'
import { formatFoodCategory, resolveFoodCategory } from '../../../shared/utils/formatters'
import { categoryLabel, foodName } from '../explanations/buildExplanation'
import {
  loadStoredRecommendations,
  pollRecommendationRefresh,
  runRecommendationRefreshPipeline,
  shouldSkipBackgroundRefresh,
  startRecommendationRefreshJob,
} from '../utils/recommendationFetchFlow'
import {
  readRecommendationsSessionCache,
  writeRecommendationsSessionCache,
} from '../utils/recommendationsSessionCache'

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

const PROFILE_REGEN_DEBOUNCE_MS = 80

function initialRecommendationsForUser(userId: number | undefined): Recommendation[] {
  if (userId == null || userId <= 0) return []
  return readRecommendationsSessionCache(userId) ?? []
}

const Recommendations = ({ user, refreshKey }: RecommendationsProps) => {
  const { t, i18n: i18nHook } = useTranslation()
  const language = i18nHook.language
  const [recommendations, setRecommendations] = useState<Recommendation[]>(() =>
    initialRecommendationsForUser(user.id)
  )
  const [loading, setLoading] = useState(() => initialRecommendationsForUser(user.id).length === 0)
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

  const applyRecommendationList = useCallback((data: unknown[], fetchId: number) => {
    if (fetchId !== latestFetchIdRef.current) return
    if (!Array.isArray(data) || data.length === 0) return
    const list = data as Recommendation[]
    setRecommendations(list)
    setSelectedCategory('all')
    setVisibleCount(Math.min(10, list.length))
    setError(null)
    if (user.id) writeRecommendationsSessionCache(user.id, list)
  }, [user.id])

  const runBackgroundRefresh = useCallback(
    async (forceRegenerate: boolean, fetchId: number) => {
      const uid = user.id
      if (uid == null) return
      try {
        await startRecommendationRefreshJob(uid, forceRegenerate)
        if (fetchId !== latestFetchIdRef.current) return

        await pollRecommendationRefresh(uid, {
          forceRegenerate,
          isCancelled: () => fetchId !== latestFetchIdRef.current,
          onFailed: (message) => {
            if (fetchId === latestFetchIdRef.current) {
              setBackgroundRefreshNote(message)
            }
          },
          onTimeout: () => {
            if (fetchId === latestFetchIdRef.current) {
              setBackgroundRefreshNote(i18n.t('recommendations.backgroundRefresh'))
            }
          },
        })

        if (fetchId !== latestFetchIdRef.current) return

        let data: unknown[]
        try {
          data = await loadStoredRecommendations(uid)
        } catch {
          data = []
        }
        if (Array.isArray(data) && data.length > 0) {
          applyRecommendationList(data, fetchId)
        }
      } catch (err: unknown) {
        console.error('Eroare la actualizarea recomandărilor în fundal:', err)
        if (fetchId === latestFetchIdRef.current && recommendationsRef.current.length === 0) {
          setError(humanizeRecommendationClientError(err))
        }
      } finally {
        if (fetchId === latestFetchIdRef.current) {
          setRegeneratingAfterProfile(false)
        }
      }
    },
    [applyRecommendationList, user.id]
  )

  const fetchRecommendations = useCallback(async (forceRegenerate: boolean = false) => {
    const fetchId = ++latestFetchIdRef.current
    let hasVisibleList = recommendationsRef.current.length > 0
    try {
      if (!user.id) {
        if (fetchId !== latestFetchIdRef.current) return
        setError(i18n.t('recommendations.errors.noUserId'))
        setLoading(false)
        setRegeneratingAfterProfile(false)
        return
      }

      setError(null)
      setBackgroundRefreshNote(null)

      const sessionCached = readRecommendationsSessionCache(user.id)
      if (sessionCached?.length) {
        setRecommendations(sessionCached)
        hasVisibleList = true
        setLoading(false)
      }

      try {
        const stored = await loadStoredRecommendations(user.id)
        if (fetchId !== latestFetchIdRef.current) return
        if (Array.isArray(stored) && stored.length > 0) {
          applyRecommendationList(stored, fetchId)
          hasVisibleList = true
          setLoading(false)
        }
      } catch {
        /* listStored — continuăm cu refresh în fundal dacă e cazul */
      }

      if (hasVisibleList) {
        try {
          const meta = await recommendationsService.getSyncMeta(user.id)
          if (fetchId !== latestFetchIdRef.current) return
          if (shouldSkipBackgroundRefresh(meta, false)) {
            setRegeneratingAfterProfile(false)
            setError(null)
            return
          }
        } catch {
          /* meta indisponibil — verificăm refresh în fundal */
        }
      }

      if (hasVisibleList) {
        setRegeneratingAfterProfile(true)
        void runBackgroundRefresh(forceRegenerate, fetchId)
        return
      }

      setLoading(true)
      setRegeneratingAfterProfile(true)
      const data = await runRecommendationRefreshPipeline(
        user.id,
        forceRegenerate,
        () => fetchId !== latestFetchIdRef.current,
        {
          onFailedNote: (message) => {
            if (fetchId === latestFetchIdRef.current) {
              setBackgroundRefreshNote(message)
            }
          },
          onTimeoutNote: () => {
            if (fetchId === latestFetchIdRef.current) {
              setBackgroundRefreshNote(i18n.t('recommendations.backgroundRefresh'))
            }
          },
        }
      )

      if (fetchId !== latestFetchIdRef.current) return
      if (Array.isArray(data) && data.length > 0) {
        applyRecommendationList(data, fetchId)
        hasVisibleList = true
      } else {
        setError(i18n.t('recommendations.errors.noneFound'))
        setRecommendations([])
      }
    } catch (err: unknown) {
      console.error('Eroare la obținerea recomandărilor:', err)
      let errorMessage = humanizeRecommendationClientError(err)
      const apiError = err as ApiErrorDetail

      if (!errorMessage || errorMessage === i18n.t('apiErrors.unexpected')) {
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
      if (!hasVisibleList) {
        setError(errorMessage)
        setRecommendations([])
      } else {
        setBackgroundRefreshNote(errorMessage)
      }
    } finally {
      if (fetchId === latestFetchIdRef.current) {
        setLoading(false)
        if (!hasVisibleList) {
          setRegeneratingAfterProfile(false)
        }
      }
    }
  }, [applyRecommendationList, runBackgroundRefresh, user.id])

  useEffect(() => {
    recommendationsRef.current = recommendations
  }, [recommendations])

  // Schimbarea limbii NU face nicio cerere: API-ul trimite fapte + nume în ambele limbi, iar cardurile, graficul și
  // categoriile își refac textul în browser (vezi explanations/buildExplanation.ts și testul languageSwitch).

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
    const mustRegenerate = hasProfileChanged || refreshKeyChanged
    const debounceMs = hasProfileChanged && !refreshKeyChanged ? PROFILE_REGEN_DEBOUNCE_MS : 0
    debounceRef.current = setTimeout(() => {
      void fetchRecommendations(mustRegenerate)
    }, debounceMs)

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
        language: currentLanguage(),
      })
    ).catch((err: unknown) => {
      console.error('Export PDF failed:', err)
    })
  }, [recommendations, user.email, user.id, user.name])

  const userId = user.id
  const categoryKeyOf = useCallback(
    (rec: Recommendation) => rec.food?.category_key ?? resolveFoodCategory(rec.food?.category)?.key ?? 'other',
    []
  )
  const categoryCounts = useMemo(
    () =>
      recommendations.reduce<Record<string, number>>((acc, rec) => {
        const key = categoryKeyOf(rec)
        acc[key] = (acc[key] || 0) + 1
        return acc
      }, {}),
    [recommendations, categoryKeyOf]
  )
  const availableCategories = useMemo(
    () => Object.keys(categoryCounts).sort((a, b) => (categoryCounts[b] || 0) - (categoryCounts[a] || 0)),
    [categoryCounts]
  )
  const categoryLabels = useMemo(() => {
    const labels: Record<string, string> = { other: t('recommendations.categoryOther') }
    const lang = language === 'en' ? 'en' : 'ro'
    for (const rec of recommendations) {
      labels[categoryKeyOf(rec)] = categoryLabel(rec, lang, formatFoodCategory)
    }
    return labels
  }, [recommendations, t, language, categoryKeyOf])
  const filteredRecommendations = useMemo(
    () =>
      selectedCategory === 'all'
        ? recommendations
        : recommendations.filter((rec) => categoryKeyOf(rec) === selectedCategory),
    [recommendations, selectedCategory, categoryKeyOf]
  )
  // Lista vine sortată după scor; „potrivirea” de pe card e scorul raportat la primul aliment (nu la categoria filtrată),
  // deci cifra afișată scade odată cu ordinea. Acoperirea nutrientului principal rămâne în textul explicației.
  const topScore = useMemo(() => Math.max(0, ...recommendations.map((r) => Number(r.score) || 0)), [recommendations])
  const matchPctOf = useCallback(
    (rec: Recommendation) => (topScore > 0 ? Math.max(1, Math.round(((Number(rec.score) || 0) / topScore) * 100)) : 0),
    [topScore]
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
      setRecommendations((current) => current.filter((r) => r.recommendation_id !== recId))
      let data: unknown
      try {
        data = await recommendationsService.replace(uid, recId, { replaceFeedbackRating: -1 })
      } catch (err) {
        setRecommendations(prev)
        throw err
      }
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data as Recommendation[])
      } else {
        setRecommendations(prev)
      }
    },
    [user.id]
  )

  const showFullPageLoader = loading && recommendations.length === 0
  const showInlineRegenerating = regeneratingAfterProfile && recommendations.length > 0

  return (
    <div className="space-y-6 sm:space-y-8">
      <RecommendationsHero
        user={user}
        count={recommendations.length}
        categories={availableCategories.length}
        bestName={recommendations[0] ? foodName(recommendations[0], i18nHook.language === 'en' ? 'en' : 'ro') : null}
        onExport={recommendations.length > 0 ? exportToPDF : undefined}
      />

      <CaloricGoalProgress
        goal={user.caloric_goal}
        recommendations={recommendations}
        warning={user.caloric_goal_warning}
      />

      {(showInlineRegenerating || backgroundRefreshNote) && (
        <GlassCard className="border-accent-border">
          <div className="flex flex-wrap items-center gap-3 text-sm text-zinc-200" role="status">
            {showInlineRegenerating && <Spinner className="h-4 w-4 shrink-0 text-accent" />}
            <p>
              {showInlineRegenerating && (
                <>
                  <span className="font-semibold text-accent">{t('recommendations.updating.title')}</span>{' '}
                  {t('recommendations.updating.body')}
                </>
              )}
              {backgroundRefreshNote && (
                <span className={showInlineRegenerating ? 'block mt-2 text-zinc-300' : ''}>
                  {backgroundRefreshNote}
                </span>
              )}
            </p>
          </div>
        </GlassCard>
      )}

      {recommendations.length > 0 && (
        <GlassCard className="w-full !max-w-none">
          <h2 className="flex items-center gap-2 text-base font-semibold text-zinc-50 sm:text-lg">
            <BarChart3 aria-hidden="true" className="h-4 w-4 text-accent" />
            {t('recommendations.chart.title')}
          </h2>
          {/* Aceeași listă (și același filtru de categorie) ca în carduri. */}
          <Suspense fallback={<ChartSkeleton />}>
            <NutrientChart recommendations={filteredRecommendations} matchPctOf={matchPctOf} />
          </Suspense>

          <div className="mt-2 border-t border-line pt-5">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
                <Filter aria-hidden="true" className="h-4 w-4 text-accent" />
                {t('recommendations.categories.title')}
              </h3>
              <p className="text-xs text-zinc-500">{t('recommendations.categories.subtitle')}</p>
            </div>
            {/* Pe telefon etichetele derulează orizontal în loc să ocupe patru rânduri. */}
            <div className="-mx-5 flex snap-x gap-2 overflow-x-auto px-5 pb-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 [&::-webkit-scrollbar]:hidden">
              <button
                type="button"
                onClick={() => {
                  setSelectedCategory('all')
                  setVisibleCount(10)
                }}
                aria-pressed={selectedCategory === 'all'}
                className={`relative min-h-[36px] flex-shrink-0 cursor-pointer snap-start whitespace-nowrap rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                  selectedCategory === 'all' ? 'border-accent-border text-accent' : 'border-line-strong text-zinc-300 hover:border-accent-border hover:text-zinc-50'
                }`}
              >
                {selectedCategory === 'all' && (
                  <span aria-hidden="true" className="absolute inset-0 animate-scale-in rounded-full bg-accent-soft" />
                )}
                <span className="relative">{t('recommendations.categories.all', { count: recommendations.length })}</span>
              </button>
              {availableCategories.map((category) => (
                <button
                  key={category}
                  type="button"
                  onClick={() => {
                    setSelectedCategory(category)
                    setVisibleCount(10)
                  }}
                  aria-pressed={selectedCategory === category}
                  className={`relative min-h-[36px] flex-shrink-0 cursor-pointer snap-start whitespace-nowrap rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                    selectedCategory === category ? 'border-accent-border text-accent' : 'border-line-strong text-zinc-300 hover:border-accent-border hover:text-zinc-50'
                  }`}
                >
                  {selectedCategory === category && (
                    <span aria-hidden="true" className="absolute inset-0 animate-scale-in rounded-full bg-accent-soft" />
                  )}
                  <span className="relative">{categoryLabels[category] ?? category} ({categoryCounts[category]})</span>
                </button>
              ))}
            </div>
          </div>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 items-stretch">
        {mainRecommendations.map((rec, index) => (
          <div key={`${rec.recommendation_id}-${rec.food_id}`} className="w-full flex">
            <RecommendationCard
              recommendation={rec}
              index={index}
              matchPct={matchPctOf(rec)}
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
                  matchPct={matchPctOf(rec)}
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
          <button
            type="button"
            onClick={() => setVisibleCount((prev) => Math.min(prev + 5, filteredRecommendations.length))}
            className="inline-flex min-h-[44px] min-w-[44px] cursor-pointer items-center justify-center rounded-lg border border-line-strong px-7 text-sm font-semibold text-zinc-100 transition-colors hover:bg-white/5 touch-manipulation"
          >
            {t('recommendations.showMore')}
          </button>
        </div>
      )}

      {showFullPageLoader && <RecommendationSkeleton label={t('recommendations.loading')} />}

      {!loading && error && recommendations.length === 0 && (
        <GlassCard className="text-center py-12">
          <p role="alert" className="mb-4 text-lg text-red-400">{error}</p>
          <p className="text-sm text-zinc-400">{t('recommendations.errors.retryHint')}</p>
        </GlassCard>
      )}

      {!loading && !error && recommendations.length === 0 && (
        <GlassCard className="text-center py-12">
          <p className="text-lg text-zinc-300">{t('recommendations.empty')}</p>
        </GlassCard>
      )}
    </div>
  )
}

export default Recommendations
