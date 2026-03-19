import { useState, useEffect } from 'react'
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

const Recommendations = ({ user, refreshKey }: RecommendationsProps) => {
  // Debug logging only in development
  if (import.meta.env.DEV) {
    console.log('Recommendations component render - user:', user)
  }
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(10)
  const [prevUserValues, setPrevUserValues] = useState({
    diet_type: user.diet_type,
    activity_level: user.activity_level,
    allergies: user.allergies,
    medical_conditions: user.medical_conditions,
    age: user.age,
    sex: user.sex,
    weight: user.weight,
    height: user.height,
  })

  const fetchRecommendations = async (forceRegenerate: boolean = false) => {
    try {
      if (import.meta.env.DEV) {
        console.log('fetchRecommendations called for user.id:', user.id, 'forceRegenerate:', forceRegenerate)
      }
      setLoading(true)
      setError(null)
      if (!user || !user.id) {
        console.error('User sau user.id lipsește!', user)
        setError('ID-ul utilizatorului lipsește. Vă rugăm să vă conectați din nou.')
        setLoading(false)
        return
      }
      
      const data = await recommendationsService.get(user.id, forceRegenerate)
      if (import.meta.env.DEV) {
        console.log('Recomandări primite:', data)
      }
      
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data)
        setVisibleCount(Math.min(10, data.length))
        setError(null)
      } else {
        if (import.meta.env.DEV) {
          console.log('Nu s-au găsit recomandări sau array-ul este gol')
        }
        setError('Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele medicale.')
        setRecommendations([])
      }
    } catch (err) {
      console.error('Eroare la obținerea recomandărilor:', err)
      // Extrage mesajul de eroare - axios interceptor-ul ar trebui să-l extragă deja
      let errorMessage = 'Nu s-au putut genera recomandări. Vă rugăm să încercați din nou.'

      if (err instanceof Error && err.message) {
        errorMessage = err.message
      } else if ((err as any)?.response?.data?.detail) {
        const detail = (err as any).response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail)
        }
      }
      
      setError(errorMessage)
      setRecommendations([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const hasChanged = 
      prevUserValues.diet_type !== user.diet_type ||
      prevUserValues.activity_level !== user.activity_level ||
      prevUserValues.allergies !== user.allergies ||
      prevUserValues.medical_conditions !== user.medical_conditions ||
      prevUserValues.age !== user.age ||
      prevUserValues.sex !== user.sex ||
      prevUserValues.weight !== user.weight ||
      prevUserValues.height !== user.height

    if (hasChanged) {
      // Regenerează recomandările dacă s-au schimbat criteriile
      fetchRecommendations(true)
      setPrevUserValues({
        diet_type: user.diet_type,
        activity_level: user.activity_level,
        allergies: user.allergies,
        medical_conditions: user.medical_conditions,
        age: user.age,
        sex: user.sex,
        weight: user.weight,
        height: user.height,
      })
    } else {
      // Altfel, doar încarcă recomandările existente
      fetchRecommendations(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id, user.diet_type, user.activity_level, user.allergies, user.medical_conditions, user.age, user.sex, user.weight, user.height])

  // Dacă s-au salvat analizele medicale sau s-a făcut update de profil și s-a incrementat refreshKey,
  // forțează regenerarea recomandărilor (include și cache invalidation pe backend).
  useEffect(() => {
    if (refreshKey && refreshKey > 0) {
      fetchRecommendations(true)
      setVisibleCount(10)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])


  const exportToPDF = () => {
    downloadRecommendationPdf({
      user: { name: user.name, email: user.email, id: user.id },
      recommendations,
    }).catch((err) => {
      console.error('Export PDF failed:', err)
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neonCyan mx-auto mb-4"></div>
          <p className="text-slate-300">Se generează recomandările personalizate...</p>
        </div>
      </div>
    )
  }

  if (error && !loading) {
    return (
      <GlassCard className="w-full max-w-full md:max-w-2xl mx-auto">
        <div className="text-center text-red-400">
          <p className="mb-4 text-base sm:text-sm break-words">{error}</p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
            <motion.button 
              onClick={() => fetchRecommendations(true)} 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border border-neonCyan/50 bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta px-4 py-3 text-sm font-semibold text-slate-950 shadow-neon transition hover:shadow-neon-magenta touch-manipulation"
            >
              Încearcă din nou
            </motion.button>
            {recommendations.length > 0 && (
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-4 py-3 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)] touch-manipulation"
              >
                <Download className="w-5 h-5 text-neonCyan" />
                <span>Exportă PDF</span>
              </motion.button>
            )}
          </div>
        </div>
      </GlassCard>
    )
  }

  // Error boundary - dacă nu există user sau id
  if (!user || !user.id) {
    return (
      <div className="w-full text-center py-12">
        <p className="text-red-400">Eroare: ID utilizator lipsă. Reconectează-te.</p>
      </div>
    )
  }

  const userId = user.id
  const visibleRecommendations = recommendations.slice(0, visibleCount)
  const tailCount = visibleRecommendations.length % 3
  const mainCount = tailCount === 0 ? visibleRecommendations.length : visibleRecommendations.length - tailCount
  const mainRecommendations = visibleRecommendations.slice(0, mainCount)
  const tailRecommendations = visibleRecommendations.slice(mainCount)

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

      {/* Cardurile individuale de recomandări */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 items-stretch">
        {mainRecommendations.map((rec, index) => (
          <div key={`${rec.recommendation_id}-${rec.food_id}`} className="w-full flex">
            <RecommendationCard
              recommendation={rec}
              index={index}
              userId={userId}
              onFeedbackSent={(recId, _rating, newLikes, newDislikes) => {
                setRecommendations((prev) =>
                  prev.map((r) =>
                    r.recommendation_id === recId
                      ? {
                          ...r,
                          feedback: { ...(r.feedback || { likes: 0, dislikes: 0 }), likes: newLikes, dislikes: newDislikes },
                          my_rating: _rating,
                        }
                      : r
                  )
                )
              }}
              onReplaceRequested={async (recId) => {
                const data = await recommendationsService.replace(userId, recId)
                if (Array.isArray(data) && data.length > 0) {
                  setRecommendations(data)
                } else {
                  await fetchRecommendations(false)
                }
              }}
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
                  onFeedbackSent={(recId, _rating, newLikes, newDislikes) => {
                    setRecommendations((prev) =>
                      prev.map((r) =>
                        r.recommendation_id === recId
                          ? {
                              ...r,
                              feedback: { ...(r.feedback || { likes: 0, dislikes: 0 }), likes: newLikes, dislikes: newDislikes },
                              my_rating: _rating,
                            }
                          : r
                      )
                    )
                  }}
                  onReplaceRequested={async (recId) => {
                    const data = await recommendationsService.replace(userId, recId)
                    if (Array.isArray(data) && data.length > 0) {
                      setRecommendations(data)
                    } else {
                      await fetchRecommendations(false)
                    }
                  }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {recommendations.length > visibleCount && (
        <div className="flex justify-center mt-8 mb-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setVisibleCount((prev) => Math.min(prev + 5, recommendations.length))}
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

