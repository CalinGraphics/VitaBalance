import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { motion } from 'framer-motion'
import { UtensilsCrossed, Download } from 'lucide-react'
import { GlassCard } from '../../../shared/components'
import { recommendationsService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import NutrientChart from './NutrientChart'
import UserProfileInfo from './UserProfileInfo'
import { downloadRecommendationPdf } from '../pdf/exportRecommendationPdf'

interface Recommendation {
  food_id: number
  food: {
    id: number
    name: string
    category: string
    image_url?: string
  }
  score: number
  coverage: number
  explanation: {
    text: string
    portion: number
    reasons: string[]
    tips?: string[]
    alternatives?: string[]
  }
  recommendation_id: number
  feedback?: {
    likes: number
    dislikes: number
  }
  my_rating?: number | null
}

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

const Recommendations = ({ user, refreshKey }: RecommendationsProps) => {
  // Debug logging only in development
  if (import.meta.env.DEV) {
    console.log('Recommendations component render - user:', user)
  }
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(10)
  const [selectedCategory, setSelectedCategory] = useState<'all' | string>('all')
  const latestFetchIdRef = useRef(0)
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

  const fetchRecommendations = useCallback(async (forceRegenerate: boolean = false) => {
    const fetchId = ++latestFetchIdRef.current
    try {
      if (import.meta.env.DEV) {
        console.log('fetchRecommendations called for user.id:', user.id, 'forceRegenerate:', forceRegenerate)
      }
      setLoading(true)
      setError(null)
      if (!user.id) {
        console.error('User id lipsește la generarea recomandărilor')
        if (fetchId !== latestFetchIdRef.current) return
        setError('ID-ul utilizatorului lipsește. Vă rugăm să vă conectați din nou.')
        setLoading(false)
        return
      }
      
      const data = await recommendationsService.get(user.id, forceRegenerate)
      if (import.meta.env.DEV) {
        console.log('Recomandări primite:', data)
      }
      
      if (fetchId !== latestFetchIdRef.current) return
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data)
        setSelectedCategory('all')
        setVisibleCount(Math.min(10, data.length))
        setError(null)
      } else {
        if (import.meta.env.DEV) {
          console.log('Nu s-au găsit recomandări sau array-ul este gol')
        }
        setError('Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele medicale.')
        setRecommendations([])
      }
    } catch (err: unknown) {
      console.error('Eroare la obținerea recomandărilor:', err)
      // Extrage mesajul de eroare - axios interceptor-ul ar trebui să-l extragă deja
      let errorMessage = 'Nu s-au putut genera recomandări. Vă rugăm să încercați din nou.'
      const apiError = err as ApiErrorDetail

      if (err instanceof Error && err.message) {
        errorMessage = err.message
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
      
      if (fetchId !== latestFetchIdRef.current) return
      setError(errorMessage)
      setRecommendations([])
    } finally {
      if (fetchId === latestFetchIdRef.current) {
        setLoading(false)
      }
    }
  }, [user.id])

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

    fetchRecommendations(hasProfileChanged || refreshKeyChanged)

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
    refreshKey,
  ])


  const exportToPDF = useCallback(() => {
    downloadRecommendationPdf({
      user: { name: user.name, email: user.email, id: user.id },
      recommendations,
    }).catch((err) => {
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
    (recId: number, rating: number, newLikes: number, newDislikes: number) => {
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
      const data = await recommendationsService.replace(userId, recId)
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data)
      } else {
        await fetchRecommendations(false)
      }
    },
    [fetchRecommendations, userId]
  )

  return (
    <div className="space-y-8">
      {/* Date profil utilizator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <UserProfileInfo user={user} />
      </motion.div>

      {/* Graficul ocupă aceeași lățime ca și cardul de profil utilizator */}
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

      {/* Cardurile individuale de recomandări */}
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

      {loading && (
        <GlassCard className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neonCyan mb-4"></div>
          <p className="text-slate-300 text-lg">
            Se încarcă recomandările...
          </p>
        </GlassCard>
      )}

      {!loading && error && (
        <GlassCard className="text-center py-12">
          <p className="text-red-400 text-lg mb-4">
            {error}
          </p>
          <button
            onClick={() => fetchRecommendations(true)}
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

