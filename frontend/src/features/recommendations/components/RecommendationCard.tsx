import { memo, useId, useMemo, useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, CheckCircle2, ChevronDown, Flame, Info, Lightbulb, ThumbsUp, ThumbsDown, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard } from '../../../shared/components'
import { formatFoodCategory } from '../../../shared/utils/formatters'
import { feedbackService } from '../../../services/api'
import { estimatePortionCalories } from '../utils/calories'
import { buildExplanation, categoryLabel, foodName, sourcesLine } from '../explanations/buildExplanation'
import type { Language } from '../../../shared/i18n'
import type { Recommendation } from '../types'

function Section({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-accent/85">{title}</p>
      <ul className="m-0 list-none space-y-2 pl-0">
        {items.map((item, idx) => (
          <li key={idx} className="flex gap-2.5 break-words text-base leading-relaxed text-zinc-200 sm:text-sm">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent/90" aria-hidden />
            <span className="min-w-0">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

interface RecommendationCardProps {
  recommendation: Recommendation
  index: number
  /** Scorul raportat la primul aliment din listă (0–100): scade odată cu ordinea cardurilor. */
  matchPct: number
  userId?: number
  onFeedbackSent?: (recId: number, rating: number | null, newLikes: number, newDislikes: number) => void
  onReplaceRequested?: (recId: number) => Promise<void>
}

const RecommendationCard = ({
  recommendation,
  matchPct,
  userId,
  onFeedbackSent,
  onReplaceRequested,
}: RecommendationCardProps) => {
  const { t, i18n } = useTranslation()
  // Textul se construiește în browser din fapte: schimbarea limbii nu face nicio cerere la server.
  const lang: Language = i18n.language === 'en' ? 'en' : 'ro'
  const { feedback, facts } = recommendation
  const explanation = useMemo(() => buildExplanation(recommendation, lang), [recommendation, lang])
  const name = foodName(recommendation, lang)
  const category = categoryLabel(recommendation, lang, formatFoodCategory)
  const portionText = facts ? `${facts.portion.amount} ${facts.portion.unit === 'ml' ? 'ml' : 'g'}` : '—'
  const portionKcal = estimatePortionCalories(recommendation)
  const [feedbackStatus, setFeedbackStatus] = useState<'idle' | 'sent' | 'error'>('idle')
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false)
  const [myRating, setMyRating] = useState<number | undefined | null>(recommendation.my_rating)
  const [localCounts, setLocalCounts] = useState(feedback ? { ...feedback } : { likes: 0, dislikes: 0 })
  const [showDislikeModal, setShowDislikeModal] = useState(false)
  const [replaceLoading, setReplaceLoading] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const detailsId = useId()
  const hasDetails =
    explanation.nutrients.length + explanation.why.length + explanation.tips.length +
      explanation.alternatives.length + explanation.sources.length > 0

  useEffect(() => {
    setMyRating(recommendation.my_rating)
    setLocalCounts(recommendation.feedback ? { ...recommendation.feedback } : { likes: 0, dislikes: 0 })
  }, [recommendation.recommendation_id, recommendation.my_rating, recommendation.feedback])

  const counts = localCounts

  const sendFeedback = async (rating: number): Promise<boolean> => {
    if (!userId || !recommendation.recommendation_id || feedbackSubmitting) return false
    setFeedbackSubmitting(true)
    setFeedbackError(null)

    const rollbackRating = myRating
    const rollbackCounts = { ...counts }
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

    try {
      await feedbackService.create({
        user_id: userId,
        recommendation_id: recommendation.recommendation_id,
        rating,
        food_id: recommendation.food_id,
      })
      onFeedbackSent?.(recommendation.recommendation_id, rating, newLikes, newDislikes)
      return true
    } catch (err: unknown) {
      setMyRating(rollbackRating)
      setLocalCounts(rollbackCounts)
      setFeedbackStatus('error')
      const msg =
        (err as { message?: string })?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('recommendations.card.errors.feedback')
      setFeedbackError(msg)
      return false
    } finally {
      setFeedbackSubmitting(false)
    }
  }

  const handleDislikeClick = () => {
    setShowDislikeModal(true)
  }

  const applyDislikeOptimistic = () => {
    const prev = myRating
    let newLikes = counts.likes
    let newDislikes = counts.dislikes
    if (prev !== undefined && prev !== null) {
      if (prev >= 4) newLikes -= 1
      else if (prev <= 2) newDislikes -= 1
    }
    newDislikes += 1
    setLocalCounts({ likes: newLikes, dislikes: newDislikes })
    setMyRating(-1)
    setFeedbackStatus('sent')
    setFeedbackError(null)
    onFeedbackSent?.(recommendation.recommendation_id, -1, newLikes, newDislikes)
    return { prev, rollbackCounts: { ...counts } }
  }

  const handleDislikeConfirm = async (replace: boolean) => {
    setShowDislikeModal(false)
    if (!userId || !recommendation.recommendation_id) return

    const { prev, rollbackCounts } = applyDislikeOptimistic()

    if (!replace) {
      setFeedbackSubmitting(true)
      try {
        await feedbackService.create({
          user_id: userId,
          recommendation_id: recommendation.recommendation_id,
          rating: -1,
          food_id: recommendation.food_id,
        })
      } catch (err: unknown) {
        setMyRating(prev)
        setLocalCounts(rollbackCounts)
        setFeedbackStatus('error')
        const msg =
          (err as { message?: string })?.message ||
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          t('recommendations.card.errors.dislike')
        setFeedbackError(msg)
        onFeedbackSent?.(
          recommendation.recommendation_id,
          prev ?? null,
          rollbackCounts.likes,
          rollbackCounts.dislikes
        )
      } finally {
        setFeedbackSubmitting(false)
      }
      return
    }

    setReplaceLoading(true)
    try {
      if (onReplaceRequested) {
        await onReplaceRequested(recommendation.recommendation_id)
      }
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        t('recommendations.card.errors.replace')
      setFeedbackError(msg)
      setFeedbackStatus('error')
    } finally {
      setReplaceLoading(false)
    }
  }

  const handleDislikeCancel = () => {
    setShowDislikeModal(false)
  }

  useEffect(() => {
    if (!showDislikeModal) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowDislikeModal(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [showDislikeModal])

  const hasLiked = myRating !== undefined && myRating !== null && myRating >= 4
  const hasDisliked = myRating !== undefined && myRating !== null && myRating <= 2

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        className="h-full"
      >
        <GlassCard className="h-full min-h-[440px] flex flex-col hover:border-line-strong transition-colors duration-200">
          {/* Conținut principal */}
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-start justify-between mb-4 min-w-0">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <h3 className="text-lg sm:text-xl font-semibold tracking-tight text-zinc-50 break-words">{name}</h3>
                  <span className="flex-shrink-0 rounded-md border border-accent-border bg-accent-soft px-2.5 py-0.5 text-xs font-medium text-accent">
                    {category}
                  </span>
                </div>
                <p className="text-base sm:text-sm text-zinc-300 mb-3 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span>
                    {t('recommendations.card.portion')}{' '}
                    <strong className="text-accent">{portionText}</strong>
                  </span>
                  {portionKcal != null && (
                    <span
                      className="inline-flex items-center gap-1 text-zinc-400"
                      title={t('recommendations.card.kcalHint')}
                    >
                      <Flame aria-hidden="true" className="h-3.5 w-3.5" />
                      <span className="tabular-nums">≈ {portionKcal} kcal</span>
                    </span>
                  )}
                </p>
                <div className="mb-4 min-w-0" title={t('recommendations.card.matchHint')}>
                  <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-400">
                    {t('recommendations.card.match')}
                  </p>
                  <div className="flex items-center gap-2 min-w-0">
                    <div
                      className="flex-1 min-w-0 bg-white/10 rounded-full h-3 sm:h-2.5 overflow-hidden"
                      role="meter"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={matchPct}
                      aria-label={t('recommendations.card.match')}
                    >
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${matchPct}%` }}
                        transition={{ duration: 0.22, ease: 'easeOut' }}
                        className="bg-accent h-3 sm:h-2.5 rounded-full"
                      />
                    </div>
                    <span className="text-base sm:text-sm font-semibold text-accent min-w-[56px] text-right tabular-nums">
                      {matchPct}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Explicație: construită din fapte + șabloanele din locales. Rezumatul și avertismentele rămân mereu
                vizibile; detaliile și sfaturile se deschid la cerere, ca lista să rămână ușor de parcurs. */}
            <div className="mb-4 rounded-lg border border-line bg-white/[0.03] p-4">
              <Section title={t('recommendations.card.summary')} items={explanation.summary} />
            </div>

            {explanation.warnings.length > 0 && (
              <div role="note" className="mb-4 rounded-lg border border-amber-400/30 bg-amber-400/[0.06] p-3">
                <p className="mb-1.5 flex items-center gap-2 text-sm font-semibold text-amber-200">
                  <AlertTriangle aria-hidden="true" className="h-4 w-4 flex-shrink-0" />
                  {t('recommendations.card.warningTitle')}
                </p>
                <ul className="space-y-1 text-sm text-amber-100/90">
                  {explanation.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {hasDetails && (
              <>
                <button
                  type="button"
                  onClick={() => setShowDetails((v) => !v)}
                  aria-expanded={showDetails}
                  aria-controls={detailsId}
                  className="mt-1 flex min-h-[44px] w-full cursor-pointer items-center justify-between rounded-lg border border-line px-4 text-sm font-medium text-zinc-200 transition-colors hover:border-accent-border hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
                >
                  {showDetails ? t('recommendations.card.hideDetails') : t('recommendations.card.showDetails')}
                  <ChevronDown
                    aria-hidden="true"
                    className={`h-4 w-4 transition-transform duration-200 ${showDetails ? 'rotate-180' : ''}`}
                  />
                </button>
                {showDetails && (
                  <div id={detailsId} className="mt-4">
                    {explanation.nutrients.length > 0 && (
                      <div className="mb-4 rounded-lg border border-line bg-white/[0.03] p-4">
                        <Section title={t('recommendations.card.nutrientDetail')} items={explanation.nutrients} />
                      </div>
                    )}
                    {explanation.why.length > 0 && (
                      <div className="mb-4 space-y-2">
                        <p className="text-base sm:text-sm font-semibold text-accent mb-3 flex items-center gap-2">
                          <CheckCircle2 aria-hidden="true" className="w-4 h-4 flex-shrink-0" />
                          {t('recommendations.card.whyTitle')}
                        </p>
                        <ul className="space-y-2">
                          {explanation.why.map((reason, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-base sm:text-sm text-zinc-300 leading-relaxed break-words">
                              <CheckCircle2 className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                              <span className="leading-relaxed">{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {explanation.tips.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-line">
                        <p className="text-base sm:text-sm font-semibold text-zinc-200 mb-2 flex items-center gap-2">
                          <Info aria-hidden="true" className="w-4 h-4 flex-shrink-0 text-accent" />
                          {t('recommendations.card.howTitle')}
                        </p>
                        <ul className="space-y-2">
                          {explanation.tips.map((tip, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-base sm:text-sm text-zinc-300 bg-white/[0.03] border border-line p-3 rounded-lg break-words">
                              <Lightbulb aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
                              <span>{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {explanation.alternatives.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-line">
                        <p className="text-base sm:text-sm font-semibold text-zinc-200 mb-2">{t('recommendations.card.alternatives')}</p>
                        <p className="text-base sm:text-sm text-zinc-300 break-words">{explanation.alternatives.join(', ')}</p>
                      </div>
                    )}
                    {explanation.sources.length > 0 && (
                      <p className="mt-4 text-[11px] leading-relaxed text-zinc-500">{sourcesLine(lang, explanation.sources)}</p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Zona de feedback fixată la baza cardului */}
          <div className="mt-auto pt-4">
            <div className="flex flex-row items-center justify-between">
              <p className="text-xs sm:text-sm text-zinc-300">
                {t('recommendations.card.feedbackQuestion')}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => sendFeedback(5)}
                  aria-label={t('recommendations.card.like')}
                  aria-pressed={hasLiked}
                  disabled={feedbackSubmitting || replaceLoading || hasLiked}
                  className={`min-h-[40px] inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold touch-manipulation transition-colors ${
                    hasLiked
                      ? 'border-accent-border bg-accent-soft text-accent cursor-default'
                      : 'border-line-strong text-zinc-300 hover:bg-accent-soft hover:text-accent disabled:opacity-60 disabled:cursor-default'
                  }`}
                >
                  <ThumbsUp className="w-4 h-4 flex-shrink-0" />
                  <span className="tabular-nums font-bold">{counts.likes}</span>
                </button>
                <button
                  type="button"
                  onClick={handleDislikeClick}
                  aria-label={t('recommendations.card.dislike')}
                  aria-pressed={hasDisliked}
                  disabled={feedbackSubmitting || replaceLoading || hasDisliked}
                  className={`min-h-[40px] inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold touch-manipulation transition-colors ${
                    hasDisliked
                      ? 'border-red-500/40 bg-red-500/10 text-red-300 cursor-default'
                      : 'border-line-strong text-zinc-300 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-60 disabled:cursor-default'
                  }`}
                >
                  <ThumbsDown className="w-4 h-4 flex-shrink-0" />
                  <span className="tabular-nums font-bold">{counts.dislikes}</span>
                </button>
              </div>
            </div>

            {feedbackStatus === 'sent' && (
              <p className="mt-2 text-xs text-accent">
                {t('recommendations.card.thanks')}
              </p>
            )}
            {feedbackStatus === 'error' && feedbackError && (
              <p className="mt-2 text-xs text-red-300">{feedbackError}</p>
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
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70"
            onClick={(e) => e.target === e.currentTarget && handleDislikeCancel()}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              role="dialog"
              aria-modal="true"
              aria-labelledby="dislike-dialog-title"
              className="w-full max-w-sm rounded-card border border-line-strong bg-surface p-6 shadow-pop"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 id="dislike-dialog-title" className="text-lg font-semibold text-zinc-50">{t('recommendations.card.dislikeTitle')}</h3>
                <button
                  type="button"
                  onClick={handleDislikeCancel}
                  aria-label={t('common.close')}
                  className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-white/10 hover:text-zinc-100"
                >
                  <X aria-hidden="true" className="w-5 h-5" />
                </button>
              </div>
              <p className="text-zinc-300 text-sm mb-5">
                {t('recommendations.card.dislikeBody')}
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => handleDislikeConfirm(true)}
                  disabled={replaceLoading}
                  className="flex-1 min-h-[44px] cursor-pointer rounded-lg bg-accent text-center text-sm font-semibold text-accent-fg transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {replaceLoading ? t('recommendations.card.replacing') : t('recommendations.card.yes')}
                </button>
                <button
                  type="button"
                  onClick={() => handleDislikeConfirm(false)}
                  disabled={replaceLoading}
                  className="flex-1 min-h-[44px] cursor-pointer rounded-lg border border-line-strong text-center text-sm font-semibold text-zinc-200 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {t('recommendations.card.no')}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

// Memoizat: un vot sau înlocuirea unui card nu redesenează celelalte carduri.
export default memo(RecommendationCard)
