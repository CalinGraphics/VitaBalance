import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Info, ThumbsUp, ThumbsDown, X } from 'lucide-react'
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
    my_rating?: number | null
  }
  index: number
  userId: number
  onFeedbackSent?: (recId: number, rating: number, newLikes: number, newDislikes: number) => void
  onReplaceRequested?: (recId: number) => Promise<void>
}

const RecommendationCard = ({
  recommendation,
  index,
  userId,
  onFeedbackSent,
  onReplaceRequested,
}: RecommendationCardProps) => {
  const { food, explanation, coverage, feedback } = recommendation
  const [feedbackStatus, setFeedbackStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle')
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [myRating, setMyRating] = useState<number | undefined | null>(recommendation.my_rating)
  const [localCounts, setLocalCounts] = useState(feedback ? { ...feedback } : { likes: 0, dislikes: 0 })
  const [showDislikeModal, setShowDislikeModal] = useState(false)
  const [replaceLoading, setReplaceLoading] = useState(false)

  useEffect(() => {
    setMyRating(recommendation.my_rating)
    setLocalCounts(recommendation.feedback ? { ...recommendation.feedback } : { likes: 0, dislikes: 0 })
  }, [recommendation.recommendation_id, recommendation.my_rating, recommendation.feedback?.likes, recommendation.feedback?.dislikes])

  const counts = localCounts

  const sendFeedback = async (rating: number): Promise<boolean> => {
    if (!userId || !recommendation.recommendation_id) return false
    setFeedbackStatus('sending')
    setFeedbackError(null)
    try {
      await feedbackService.create({
        user_id: userId,
        recommendation_id: recommendation.recommendation_id,
        rating,
        tried: true,
      })
      const prev = myRating
      let newLikes = counts.likes
      let newDislikes = counts.dislikes
      if (prev !== undefined && prev !== null) {
        if (prev >= 4) newLikes -= 1
        else if (prev <= 2) newDislikes -= 1
      }
      if (rating >= 4) newLikes += 1
      else if (rating <= 2) newDislikes += 1
      setLocalCounts({ likes: newLikes, dislikes: newDislikes })
      setMyRating(rating)
      setFeedbackStatus('sent')
      onFeedbackSent?.(recommendation.recommendation_id, rating, newLikes, newDislikes)
      return true
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Nu s-a putut trimite feedback-ul. Încearcă din nou.'
      setFeedbackError(msg)
      setFeedbackStatus('error')
      return false
    }
  }

  const handleDislikeClick = () => {
    setShowDislikeModal(true)
  }

  const handleDislikeConfirm = async (replace: boolean) => {
    setReplaceLoading(true)
    setShowDislikeModal(false)
    try {
      const ok = await sendFeedback(1)
      if (ok && replace && onReplaceRequested) {
        await onReplaceRequested(recommendation.recommendation_id)
      }
    } finally {
      setReplaceLoading(false)
    }
  }

  const handleDislikeCancel = () => {
    setShowDislikeModal(false)
  }

  const hasLiked = myRating !== undefined && myRating !== null && myRating >= 4
  const hasDisliked = myRating !== undefined && myRating !== null && myRating <= 2

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.04, duration: 0.22, ease: 'easeOut' }}
        className="h-full"
      >
        <GlassCard className="h-full min-h-[520px] flex flex-col hover:shadow-neon transition-all duration-300">
          {/* Conținut principal */}
          <div className="flex-1">
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
                  Porție sugerată: <strong className="text-neonCyan">{explanation.portion}g</strong>
                </p>
                <div className="flex items-center gap-2 mb-4 min-w-0">
                  <div className="flex-1 min-w-0 bg-slate-800 rounded-full h-3 sm:h-2.5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(coverage, 100)}%` }}
                      transition={{ delay: index * 0.04 + 0.15, duration: 0.35, ease: 'easeOut' }}
                      className="bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta h-3 sm:h-2.5 rounded-full shadow-neon"
                    />
                  </div>
                  <span className="text-base sm:text-sm font-semibold text-neonCyan min-w-[56px] text-right tabular-nums">
                    {coverage.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="mb-5 p-4 rounded-xl bg-slate-800/50 border border-neonCyan/20">
              <p className="text-slate-200 text-base sm:text-sm leading-relaxed break-words">{faraPrefixContext(explanation.text)}</p>
            </div>

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
                      transition={{ delay: index * 0.02 + idx * 0.03, duration: 0.18, ease: 'easeOut' }}
                      className="flex items-start gap-2 text-base sm:text-sm text-slate-300 leading-relaxed break-words"
                    >
                      <CheckCircle2 className="w-4 h-4 text-neonCyan mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed">{faraPrefixContext(reason)}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            )}

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

            {explanation.alternatives && explanation.alternatives.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <p className="text-base sm:text-sm font-semibold text-slate-200 mb-2">Alternative similare:</p>
                <p className="text-base sm:text-sm text-slate-300 break-words">{explanation.alternatives.join(', ')}</p>
              </div>
            )}
          </div>

          {/* Zona de feedback fixată la baza cardului */}
          <div className="mt-auto pt-4">
            <div className="flex flex-row items-center justify-between">
              <p className="text-xs sm:text-sm text-slate-300">
                Cum ți se pare această recomandare?
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => sendFeedback(5)}
                  disabled={feedbackStatus === 'sending' || hasLiked}
                  className={`min-h-[36px] inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold touch-manipulation transition-all ${
                    hasLiked
                      ? 'border-emerald-400 bg-emerald-500/20 text-emerald-300 cursor-default'
                      : 'border-emerald-400/50 text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-60 disabled:cursor-default'
                  }`}
                >
                  <ThumbsUp className="w-4 h-4 flex-shrink-0" />
                  <span className="tabular-nums font-bold">{counts.likes}</span>
                </button>
                <button
                  type="button"
                  onClick={handleDislikeClick}
                  disabled={feedbackStatus === 'sending' || hasDisliked}
                  className={`min-h-[36px] inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold touch-manipulation transition-all ${
                    hasDisliked
                      ? 'border-rose-400 bg-rose-500/20 text-rose-300 cursor-default'
                      : 'border-rose-400/50 text-rose-300 hover:bg-rose-500/10 disabled:opacity-60 disabled:cursor-default'
                  }`}
                >
                  <ThumbsDown className="w-4 h-4 flex-shrink-0" />
                  <span className="tabular-nums font-bold">{counts.dislikes}</span>
                </button>
              </div>
            </div>

            {feedbackStatus === 'sent' && (
              <p className="mt-2 text-xs text-emerald-300">
                Mulțumim pentru feedback, îl folosim pentru a ajusta recomandările viitoare.
              </p>
            )}
            {feedbackStatus === 'error' && feedbackError && (
              <p className="mt-2 text-xs text-rose-300">{feedbackError}</p>
            )}
          </div>
        </GlassCard>
      </motion.div>

      <AnimatePresence>
        {showDislikeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={(e) => e.target === e.currentTarget && handleDislikeCancel()}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-800 border border-neonCyan/30 rounded-xl p-6 max-w-sm w-full shadow-neon"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-100">Nu ți se potrivește?</h3>
                <button
                  type="button"
                  onClick={handleDislikeCancel}
                  className="p-1 rounded-lg hover:bg-slate-700 text-slate-400"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-slate-300 text-sm mb-5">
                Vrei să îți schimb această recomandare cu o alternativă potrivită nevoilor tale?
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => handleDislikeConfirm(true)}
                  disabled={replaceLoading}
                  className="flex-1 min-h-[44px] rounded-full border border-neonCyan/60 bg-gradient-to-r from-neonCyan/40 via-neonPurple/60 to-neonMagenta/60 text-slate-50 font-semibold shadow-[0_0_18px_rgba(0,245,255,0.5)] hover:shadow-[0_0_28px_rgba(0,245,255,0.9)] hover:brightness-110 disabled:opacity-60 disabled:cursor-not-allowed transition-all text-center"
                >
                  {replaceLoading ? 'Se înlocuiește...' : 'Da'}
                </button>
                <button
                  type="button"
                  onClick={() => handleDislikeConfirm(false)}
                  disabled={replaceLoading}
                  className="flex-1 min-h-[44px] rounded-full border border-slate-500/80 bg-slate-800/60 text-slate-200 font-semibold hover:bg-slate-700/80 hover:border-slate-300 transition-all min-w-[0] text-center"
                >
                  Nu
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default RecommendationCard
