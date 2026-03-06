import { motion } from 'framer-motion'
import { CheckCircle2, Info } from 'lucide-react'
import { GlassCard } from '../../../shared/components'
import { formatFoodCategory } from '../../../shared/utils/formatters'

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
}

const RecommendationCard = ({
  recommendation,
  index
}: RecommendationCardProps) => {
  const { food, explanation, coverage } = recommendation

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
                {formatFoodCategory(food.category)}
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

        {/* Tips - Always visible */}
        {explanation.tips && explanation.tips.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
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

        {/* Alternatives - Always visible */}
        {explanation.alternatives && explanation.alternatives.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-sm font-semibold text-slate-200 mb-2">Alternative similare:</p>
            <p className="text-sm text-slate-300">{explanation.alternatives.join(', ')}</p>
          </div>
        )}
      </GlassCard>
    </motion.div>
  )
}

export default RecommendationCard

