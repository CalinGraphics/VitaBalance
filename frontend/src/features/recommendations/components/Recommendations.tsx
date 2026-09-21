import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { UtensilsCrossed, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, PageHeader, Spinner } from '../../../shared/components'
import i18n, { currentLanguage } from '../../../shared/i18n'
import { recommendationsService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import NutrientChart from './NutrientChart'
import UserProfileInfo from './UserProfileInfo'
import CaloricGoalProgress from './CaloricGoalProgress'
import type { Recommendation } from '../types'
import { humanizeRecommendationClientError } from '../../../shared/utils/apiErrors'
import { resolveFoodCategory } from '../../../shared/utils/formatters'
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

  // Explicațiile și numele alimentelor vin din API în limba curentă: la schimbarea limbii reîncărcăm lista salvată.
  const previousLanguageRef = useRef(language)
  useEffect(() => {
    if (previousLanguageRef.current === language) return
    previousLanguageRef.current = language
    const uid = user.id
    if (!uid) return
    let cancelled = false
    loadStoredRecommendations(uid)
      .then((data) => {
        if (cancelled || !Array.isArray(data) || data.length === 0) return
        setRecommendations(data as Recommendation[])
        writeRecommendationsSessionCache(uid, data as Recommendation[])
      })
      .catch(() => {
        /* rămân textele din limba anterioară până la următoarea reîncărcare */
      })
    return () => {
      cancelled = true
    }
  }, [language, user.id])

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
    (rec: Recommendation) => resolveFoodCategory(rec.food?.category)?.key ?? 'other',
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
    for (const rec of recommendations) {
      const resolved = resolveFoodCategory(rec.food?.category)
      if (resolved) labels[resolved.key] = resolved.label
    }
    return labels
  }, [recommendations, t])
  const filteredRecommendations = useMemo(
    () =>
      selectedCategory === 'all'
        ? recommendations
        : recommendations.filter((rec) => categoryKeyOf(rec) === selectedCategory),
    [recommendations, selectedCategory, categoryKeyOf]
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
    <div className="space-y-8">
      <UserProfileInfo user={user} />

      <CaloricGoalProgress goal={user.caloric_goal} recommendations={recommendations} />

      {currentLanguage() !== 'ro' && recommendations.length > 0 && (
        <p className="-mt-4 text-xs leading-relaxed text-zinc-500">{t('recommendations.contentLanguageNote')}</p>
      )}

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
          <div className="mb-6 flex flex-col gap-4 sm:gap-6 md:flex-row md:items-center md:justify-between">
            <PageHeader
              Icon={UtensilsCrossed}
              title={t('recommendations.title')}
              subtitle={t('recommendations.subtitle')}
              className="min-w-0"
            />
            <button
              type="button"
              onClick={exportToPDF}
              className="flex min-h-[44px] min-w-[44px] cursor-pointer items-center justify-center gap-2 self-start whitespace-nowrap rounded-lg border border-line-strong px-4 text-sm font-semibold text-zinc-100 transition-colors hover:bg-white/5 touch-manipulation md:self-center"
            >
              <Download aria-hidden="true" className="h-4 w-4 flex-shrink-0 text-accent" />
              <span>{t('recommendations.exportPdf')}</span>
            </button>
          </div>

          <NutrientChart recommendations={recommendations} />
        </GlassCard>
      )}

      {recommendations.length > 0 && (
        <GlassCard className="w-full !max-w-none">
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-zinc-50">{t('recommendations.categories.title')}</h3>
            <p className="text-xs text-zinc-400">{t('recommendations.categories.subtitle')}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                setSelectedCategory('all')
                setVisibleCount(10)
              }}
              aria-pressed={selectedCategory === 'all'}
              className={`min-h-[36px] cursor-pointer rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
                selectedCategory === 'all'
                  ? 'border-accent-border bg-accent-soft text-accent'
                  : 'border-line-strong text-zinc-300 hover:bg-white/5'
              }`}
            >
              {t('recommendations.categories.all', { count: recommendations.length })}
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
                className={`min-h-[36px] cursor-pointer rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
                  selectedCategory === category
                    ? 'border-accent-border bg-accent-soft text-accent'
                    : 'border-line-strong text-zinc-300 hover:bg-white/5'
                }`}
              >
                {categoryLabels[category] ?? category} ({categoryCounts[category]})
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
          <button
            type="button"
            onClick={() => setVisibleCount((prev) => Math.min(prev + 5, filteredRecommendations.length))}
            className="inline-flex min-h-[44px] min-w-[44px] cursor-pointer items-center justify-center rounded-lg border border-line-strong px-7 text-sm font-semibold text-zinc-100 transition-colors hover:bg-white/5 touch-manipulation"
          >
            {t('recommendations.showMore')}
          </button>
        </div>
      )}

      {showFullPageLoader && (
        <GlassCard className="text-center py-12">
          <div role="status" aria-live="polite">
            <Spinner className="mb-4 h-7 w-7 text-accent" />
            <p className="text-lg text-zinc-300">{t('recommendations.loading')}</p>
          </div>
        </GlassCard>
      )}

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
