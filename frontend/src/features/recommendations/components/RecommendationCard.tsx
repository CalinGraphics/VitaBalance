import { useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, Info, ThumbsUp, ThumbsDown } from 'lucide-react'
import { GlassCard } from '../../../shared/components'
import { formatFoodCategory } from '../../../shared/utils/formatters'
import { feedbackService } from '../../../services/api'

/** Elimină prefixul [context: ...] sau [Context: ...] din textele de recomandare. */
function faraPrefixContext(s: string): string {
  if (!s || typeof s !== 'string') return ''
  return s
    .replace(/\s*\[[Cc]ontext:\s*[^\]]*\]\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

interface RecommendationCardProps {
  recommendation: {
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
  }
  index: number
  userId: number
}

const RecommendationCard = ({
  recommendation,
  index,
  userId,
}: RecommendationCardProps) => {
  const { food, explanation, coverage, feedback } = recommendation
  const [feedbackStatus, setFeedbackStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [feedbackError, setFeedbackError] = useState<string | null>(null)

  const sendFeedback = async (rating: number) => {
    if (!userId || !recommendation.recommendation_id) return
    setFeedbackStatus('sending')
    setFeedbackError(null)
    try {
      await feedbackService.create({
        user_id: userId,
        recommendation_id: recommendation.recommendation_id,
        rating,
        tried: true,
      })
      setFeedbackStatus('sent')
    } catch (err: any) {
      const msg =
        err?.message ||
        err?.response?.data?.detail ||
        'Nu s-a putut trimite feedback-ul. Încearcă din nou.'
      setFeedbackError(msg)
      setFeedbackStatus('error')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
    >
      <GlassCard className="hover:shadow-neon transition-all duration-300">
        {/* Header */}
        <div className="flex items-start justify-between mb-4 min-w-0">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h3 className="text-lg sm:text-xl font-bold text-slate-100 break-words">{food.name}</h3>
              <span className="text-xs bg-gradient-to-r from-neonCyan/20 to-neonPurple/20 text-neonCyan px-3 py-1 rounded-full border border-neonCyan/30 flex-shrink-0">
                {formatFoodCategory(food.category)}
              </span>
            </div>
            <p className="text-base sm:text-sm text-slate-300 mb-3">
              Porție sugerată: <strong className="text-neonCyan">{explanation.portion}g</strong> (cam un bol)
            </p>
            <div className="flex items-center gap-2 mb-4 min-w-0">
              <div className="flex-1 min-w-0 bg-slate-800 rounded-full h-3 sm:h-2.5 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(coverage, 100)}%` }}
                  transition={{ delay: index * 0.1 + 0.3, duration: 0.8 }}
                  className="bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta h-3 sm:h-2.5 rounded-full shadow-neon"
                />
              </div>
              <span className="text-base sm:text-sm font-semibold text-neonCyan min-w-[56px] text-right tabular-nums">
                {coverage.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Explanation - Highlighted (fără [context: ...]) */}
        <div className="mb-5 p-4 rounded-xl bg-slate-800/50 border border-neonCyan/20">
          <p className="text-slate-200 text-base sm:text-sm leading-relaxed break-words">{faraPrefixContext(explanation.text)}</p>
        </div>

        {/* De ce îl recomand – bullet-uri scurte (nu repetă paragraful de mai sus) */}
        {explanation.reasons && explanation.reasons.length > 0 && (
          <div className="mb-4 space-y-2">
            <p className="text-base sm:text-sm font-semibold text-neonPurple mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              De ce îl recomand:
            </p>
            <ul className="space-y-2">
              {explanation.reasons.map((reason, idx) => (
                <motion.li
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 + idx * 0.05 }}
                  className="flex items-start gap-2 text-base sm:text-sm text-slate-300 leading-relaxed break-words"
                >
                  <CheckCircle2 className="w-4 h-4 text-neonCyan mt-0.5 flex-shrink-0" />
                  <span className="leading-relaxed">{faraPrefixContext(reason)}</span>
                </motion.li>
              ))}
            </ul>
          </div>
        )}

        {/* Tips - Always visible (fără [context: ...]) */}
        {explanation.tips && explanation.tips.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-base sm:text-sm font-semibold text-neonMagenta mb-2 flex items-center gap-2">
              <Info className="w-4 h-4 flex-shrink-0" />
              Sfaturi
            </p>
            <ul className="space-y-2">
              {explanation.tips.map((tip, idx) => (
                <li key={idx} className="text-base sm:text-sm text-slate-300 bg-slate-800/50 border border-neonMagenta/20 p-3 rounded-lg break-words">
                  💡 {faraPrefixContext(tip)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Alternatives - Always visible */}
        {explanation.alternatives && explanation.alternatives.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-base sm:text-sm font-semibold text-slate-200 mb-2">Alternative similare:</p>
            <p className="text-base sm:text-sm text-slate-300 break-words">{explanation.alternatives.join(', ')}</p>
          </div>
        )}

        {/* Feedback buttons */}
        <div className="mt-5 pt-4 border-t border-white/10 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-400 mb-1 sm:mb-0">
            <span>Cum ți se pare această recomandare?</span>
            {feedback && (feedback.likes > 0 || feedback.dislikes > 0) && (
              <span className="inline-flex items-center gap-2 text-[11px] sm:text-xs text-slate-500">
                {feedback.likes > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3 text-emerald-400" />
                    {feedback.likes}
                  </span>
                )}
                {feedback.dislikes > 0 && (
                  <span className="inline-flex items-center gap-1">
                    <ThumbsDown className="w-3 h-3 text-rose-400" />
                    {feedback.dislikes}
                  </span>
                )}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => sendFeedback(5)}
              disabled={feedbackStatus === 'sending' || feedbackStatus === 'sent'}
              className="min-h-[36px] inline-flex items-center gap-1.5 rounded-full border border-emerald-400/50 px-3 py-1.5 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-60 disabled:cursor-default touch-manipulation"
            >
              <ThumbsUp className="w-4 h-4" />
              Îmi place
            </button>
            <button
              type="button"
              onClick={() => sendFeedback(1)}
              disabled={feedbackStatus === 'sending' || feedbackStatus === 'sent'}
              className="min-h-[36px] inline-flex items-center gap-1.5 rounded-full border border-rose-400/50 px-3 py-1.5 text-xs font-semibold text-rose-300 hover:bg-rose-500/10 disabled:opacity-60 disabled:cursor-default touch-manipulation"
            >
              <ThumbsDown className="w-4 h-4" />
              Nu prea
            </button>
          </div>
        </div>

        {feedbackStatus === 'sent' && (
          <p className="mt-2 text-xs text-emerald-300">
            Mulțumim pentru feedback, îl folosim pentru a ajusta recomandările viitoare.
          </p>
        )}
        {feedbackStatus === 'error' && feedbackError && (
          <p className="mt-2 text-xs text-rose-300">
            {feedbackError}
          </p>
        )}
      </GlassCard>
    </motion.div>
  )
}

export default RecommendationCard

