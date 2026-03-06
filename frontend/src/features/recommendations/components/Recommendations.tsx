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
}

interface RecommendationsProps {
  user: User
}

const Recommendations = ({ user }: RecommendationsProps) => {
  // Debug logging only in development
  if (import.meta.env.DEV) {
    console.log('Recommendations component render - user:', user)
  }
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [prevUserValues, setPrevUserValues] = useState({
    diet_type: user.diet_type,
    activity_level: user.activity_level,
    allergies: user.allergies,
    medical_conditions: user.medical_conditions
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
      
      if (err?.message) {
        errorMessage = err.message
      } else if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
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
      prevUserValues.medical_conditions !== user.medical_conditions

    if (hasChanged) {
      // Regenerează recomandările dacă s-au schimbat criteriile
      fetchRecommendations(true)
      setPrevUserValues({
        diet_type: user.diet_type,
        activity_level: user.activity_level,
        allergies: user.allergies,
        medical_conditions: user.medical_conditions
      })
    } else {
      // Altfel, doar încarcă recomandările existente
      fetchRecommendations(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id, user.diet_type, user.activity_level, user.allergies, user.medical_conditions])


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
      <GlassCard className="max-w-2xl mx-auto">
        <div className="text-center text-red-400">
          <p className="mb-4">{error}</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <motion.button 
              onClick={() => fetchRecommendations(true)} 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta px-4 py-2 text-sm font-semibold text-slate-950 shadow-neon transition hover:shadow-neon-magenta"
            >
              Încearcă din nou
            </motion.button>
            {recommendations.length > 0 && (
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-4 py-2.5 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 flex items-center gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)]"
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

  // Error boundary - dacă nu există user
  if (!user) {
    return (
      <div className="w-full text-center py-12">
        <p className="text-red-400">Eroare: Date utilizator lipsă</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Date profil utilizator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <UserProfileInfo user={user} />
      </motion.div>

      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="col-span-2 lg:col-span-3 xl:col-span-3"
        >
          <GlassCard className="w-full max-w-none">
            <div className="flex items-center justify-between mb-6 gap-6">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-3 rounded-lg shadow-neon">
                  <UtensilsCrossed className="w-6 h-6 text-black" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-100">Recomandările tale</h2>
                  <p className="text-slate-400 text-sm">Alimente personalizate pentru nevoile tale nutriționale</p>
                </div>
              </div>
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-5 py-2.5 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 flex items-center gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)] whitespace-nowrap"
              >
                <Download className="w-5 h-5 text-neonCyan" />
                <span>Exportă PDF</span>
              </motion.button>
            </div>

            {recommendations.length > 0 && (
              <NutrientChart recommendations={recommendations} />
            )}
          </GlassCard>
        </motion.div>
        {recommendations.map((rec, index) => (
          <RecommendationCard
            key={rec.food_id}
            recommendation={rec}
            index={index}
          />
        ))}
      </div>

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
            className="px-4 py-2 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition"
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

