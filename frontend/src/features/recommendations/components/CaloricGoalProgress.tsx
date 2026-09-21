import { useMemo } from 'react'
import { Flame } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard } from '../../../shared/components'
import type { Recommendation } from '../types'
import { sumRecommendationCalories } from '../utils/calories'

interface CaloricGoalProgressProps {
  /** Obiectivul caloric zilnic al utilizatorului (kcal). Componenta nu se afișează fără el. */
  goal: number | null | undefined
  recommendations: Recommendation[]
}

/**
 * Bară de progres informativă: caloriile porțiilor sugerate vs. obiectivul caloric setat în profil.
 * Nu influențează scorarea sau selecția recomandărilor — doar le raportează la obiectiv.
 */
const CaloricGoalProgress = ({ goal, recommendations }: CaloricGoalProgressProps) => {
  const { t } = useTranslation()
  const { total, counted } = useMemo(() => sumRecommendationCalories(recommendations), [recommendations])

  if (goal == null || !Number.isFinite(goal) || goal <= 0) return null

  const percent = Math.round((total / goal) * 100)
  const over = total > goal
  const missing = recommendations.length - counted

  return (
    <GlassCard className="w-full !max-w-none">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border border-accent-border bg-accent-soft text-accent">
          <Flame aria-hidden="true" className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <h3 id="caloric-goal-title" className="text-base font-semibold text-zinc-50">
            {t('recommendations.caloric.title')}
          </h3>
          <p className="text-xs text-zinc-400">{t('recommendations.caloric.subtitle')}</p>
        </div>
      </div>

      {counted === 0 ? (
        <p className="text-sm text-zinc-400">{t('recommendations.caloric.noData')}</p>
      ) : (
        <>
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <p className="text-sm text-zinc-300">
              <span className="text-2xl font-semibold tabular-nums text-zinc-50">≈ {total}</span>{' '}
              <span className="text-zinc-400">
                / {goal} kcal
              </span>
            </p>
            <p className={`text-sm font-semibold tabular-nums ${over ? 'text-amber-300' : 'text-accent'}`}>
              {percent}%
            </p>
          </div>

          <div
            role="progressbar"
            aria-labelledby="caloric-goal-title"
            aria-valuemin={0}
            aria-valuemax={goal}
            aria-valuenow={Math.min(total, goal)}
            aria-valuetext={t('recommendations.caloric.valueText', { total, goal, percent })}
            className="h-2.5 w-full overflow-hidden rounded-full bg-white/10"
          >
            <div
              className={`h-full rounded-full transition-[width] duration-500 ease-out ${over ? 'bg-amber-400' : 'bg-accent'}`}
              style={{ width: `${Math.min(percent, 100)}%` }}
            />
          </div>

          <p className="mt-3 text-xs leading-relaxed text-zinc-400">
            {over
              ? t('recommendations.caloric.over', { diff: total - goal })
              : t('recommendations.caloric.remaining', { diff: goal - total })}
          </p>
        </>
      )}

      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
        {t('recommendations.caloric.disclaimer', { count: counted })}
        {missing > 0 && counted > 0 ? ` ${t('recommendations.caloric.missing', { count: missing })}` : ''}
      </p>
    </GlassCard>
  )
}

export default CaloricGoalProgress
