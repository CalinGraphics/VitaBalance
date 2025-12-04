import { motion, AnimatePresence } from 'framer-motion'
import { ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Info, CheckCircle2 } from 'lucide-react'
import { useState } from 'react'
import { GlassCard } from '../../../shared/components'

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
  }
  index: number
  isExpanded: boolean
  onExpand: () => void
  onFeedback: (recommendationId: number, rating: number) => void
}

const RecommendationCard = ({
  recommendation,
  index,
  isExpanded,
  onExpand,
  onFeedback
}: RecommendationCardProps) => {
  const { food, explanation, coverage, recommendation_id } = recommendation
  const [feedbackState, setFeedbackState] = useState<'idle' | 'liked' | 'disliked' | 'loading-like' | 'loading-dislike'>('idle')

  const handleLike = async () => {
    if (feedbackState !== 'idle' && feedbackState !== 'disliked') return
    setFeedbackState('loading-like')
    try {
      await onFeedback(recommendation_id, 1)
      setFeedbackState('liked')
    } catch (error) {
      console.error('Eroare la like:', error)
      setFeedbackState('idle')
    }
  }

  const handleDislike = async () => {
    if (feedbackState !== 'idle' && feedbackState !== 'liked') return
    setFeedbackState('loading-dislike')
    try {
      await onFeedback(recommendation_id, -1) // Backend acceptă -1 pentru dislike
      setFeedbackState('disliked')
    } catch (error) {
      console.error('Eroare la dislike:', error)
      setFeedbackState('idle')
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
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h3 className="text-xl font-bold text-slate-100">{food.name}</h3>
              <span className="text-xs bg-gradient-to-r from-neonCyan/20 to-neonPurple/20 text-neonCyan px-3 py-1 rounded-full border border-neonCyan/30">
                {food.category}
              </span>
            </div>
            <p className="text-sm text-slate-300 mb-3">
              Porție sugerată: <strong className="text-neonCyan">{explanation.portion}g</strong> (cam un bol)
            </p>
            <div className="flex items-center gap-2 mb-4">
              <div className="flex-1 bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(coverage, 100)}%` }}
                  transition={{ delay: index * 0.1 + 0.3, duration: 0.8 }}
                  className="bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta h-2.5 rounded-full shadow-neon"
                />
              </div>
              <span className="text-sm font-semibold text-neonCyan min-w-[50px]">
                {coverage.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Explanation - Highlighted */}
        <div className="mb-5 p-4 rounded-xl bg-slate-800/50 border border-neonCyan/20">
          <p className="text-slate-200 text-sm leading-relaxed">{explanation.text}</p>
        </div>

        {/* Reasons */}
        <div className="mb-4 space-y-2">
          <p className="text-sm font-semibold text-neonPurple mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            De ce îl recomand:
          </p>
          <ul className="space-y-2">
            {explanation.reasons.map((reason, idx) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 + idx * 0.05 }}
                className="flex items-start gap-2 text-sm text-slate-300"
              >
                <CheckCircle2 className="w-4 h-4 text-neonCyan mt-0.5 flex-shrink-0" />
                <span className="leading-relaxed">{reason}</span>
              </motion.li>
            ))}
          </ul>
        </div>

        {/* Expandable Details */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="pt-4 border-t border-white/10 space-y-4">
                {explanation.tips && explanation.tips.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-neonMagenta mb-2 flex items-center gap-2">
                      <Info className="w-4 h-4" />
                      Sfaturi
                    </p>
                    <ul className="space-y-2">
                      {explanation.tips.map((tip, idx) => (
                        <li key={idx} className="text-sm text-slate-300 bg-slate-800/50 border border-neonMagenta/20 p-3 rounded-lg">
                          💡 {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {explanation.alternatives && explanation.alternatives.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-slate-200 mb-2">Alternative similare:</p>
                    <p className="text-sm text-slate-300">{explanation.alternatives.join(', ')}</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/10">
          <button
            onClick={onExpand}
            className="flex items-center gap-2 text-sm text-neonCyan hover:text-neonMagenta transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                Ascunde detalii
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                Vezi detalii
              </>
            )}
          </button>

          <div className="flex items-center gap-2">
            <motion.button
              onClick={handleLike}
              disabled={feedbackState === 'loading-like' || feedbackState === 'loading-dislike'}
              whileHover={{ scale: feedbackState.includes('loading') ? 1 : 1.1 }}
              whileTap={{ scale: feedbackState.includes('loading') ? 1 : 0.9 }}
              className={`p-2 rounded-lg transition-all duration-200 border ${
                feedbackState === 'liked'
                  ? 'text-green-400 bg-green-400/30 border-green-400/50 shadow-[0_0_15px_rgba(34,197,94,0.5)]'
                  : feedbackState === 'loading-like'
                  ? 'text-green-400/50 bg-green-400/10 border-green-400/20 cursor-not-allowed'
                  : 'text-green-400 hover:bg-green-400/20 border-green-400/30'
              }`}
              aria-label="Like"
            >
              {feedbackState === 'loading-like' ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-5 h-5 border-2 border-green-400 border-t-transparent rounded-full"
                />
              ) : (
                <ThumbsUp className={`w-5 h-5 ${feedbackState === 'liked' ? 'fill-current' : ''}`} />
              )}
            </motion.button>
            <motion.button
              onClick={handleDislike}
              disabled={feedbackState === 'loading-like' || feedbackState === 'loading-dislike'}
              whileHover={{ scale: feedbackState.includes('loading') ? 1 : 1.1 }}
              whileTap={{ scale: feedbackState.includes('loading') ? 1 : 0.9 }}
              className={`p-2 rounded-lg transition-all duration-200 border ${
                feedbackState === 'disliked'
                  ? 'text-red-400 bg-red-400/30 border-red-400/50 shadow-[0_0_15px_rgba(239,68,68,0.5)]'
                  : feedbackState === 'loading-dislike'
                  ? 'text-red-400/50 bg-red-400/10 border-red-400/20 cursor-not-allowed'
                  : 'text-red-400 hover:bg-red-400/20 border-red-400/30'
              }`}
              aria-label="Dislike"
            >
              {feedbackState === 'loading-dislike' ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-5 h-5 border-2 border-red-400 border-t-transparent rounded-full"
                />
              ) : (
                <ThumbsDown className={`w-5 h-5 ${feedbackState === 'disliked' ? 'fill-current' : ''}`} />
              )}
            </motion.button>
          </div>
        </div>
      </GlassCard>
    </motion.div>
  )
}

export default RecommendationCard

