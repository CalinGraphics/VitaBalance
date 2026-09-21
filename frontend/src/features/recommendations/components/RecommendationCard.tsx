import { useState, useEffect, type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, Flame, Info, Lightbulb, ThumbsUp, ThumbsDown, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard } from '../../../shared/components'
import { formatFoodCategory } from '../../../shared/utils/formatters'
import { feedbackService } from '../../../services/api'
import { formatPortionSuggestion } from '../utils/formatPortion'
import { estimatePortionCalories } from '../utils/calories'

/** Elimină prefixul [context: ...] și normalizează spațiile pe un singur rând (motivații, sfaturi). */
function faraPrefixContext(s: string): string {
  if (!s || typeof s !== 'string') return ''
  return stripContextMarker(s).replace(/[ \t]+/g, ' ').replace(/\n+/g, ' ').trim()
}

function stripContextMarker(s: string): string {
  return s.replace(/\s*\[[Cc]ontext:\s*[^\]]*\]\s*/g, ' ')
}

/** Păstrează rândurile utile pentru mesajul principal; comprimă doar spațiile orizontale. */
function normalizeExplanationRaw(s: string): string {
  if (!s || typeof s !== 'string') return ''
  return stripContextMarker(s)
    .split('\n')
    .map((line) => line.replace(/[ \t]+/g, ' ').trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

const EXPL_SECTION_SEP = '\x1e'
const LEGACY_EXPL_SECTION_SEP = '\n\n---\n\n'

function isSeparatorOnlyChunk(s: string): boolean {
  const t = s.trim()
  return t === '---' || /^-+$/.test(t) || t === '\x1e'
}

function splitExplanationSections(raw: string): string[] {
  const withLegacy = raw.split(LEGACY_EXPL_SECTION_SEP).join(EXPL_SECTION_SEP)
  return withLegacy
    .split(EXPL_SECTION_SEP)
    .map((p) => p.trim())
    .filter((p) => p && !isSeparatorOnlyChunk(p))
}

/** Scoate formulările legale de tip disclaimer din textul afișat la aliment (inclusiv date vechi din DB). */
function stripMedicalDisclaimersFromExplanation(s: string): string {
  let t = s.replace(
    /\s*Valorile sunt orientative\s*\([^)]*\)\s*;\s*nu\s+înlocuiesc consultul medical\.?\s*/gi,
    '\n'
  )
  t = t.replace(/\s*Valorile sunt orientative[^.\n]*(?:catalog|model)[^.\n]*\.?\s*/gi, '\n')
  t = t.replace(/\s*nu\s+înlocuiesc consultul medical\.?\s*/gi, '\n')
  t = t.replace(/\s*Valorile per 100 g provin[^.\n]*\.?\s*/gi, '\n')
  return t
    .split('\n')
    .filter((ln) => {
      const l = ln.toLowerCase().trim()
      if (!l) return false
      if (l.includes('valorile sunt orientative') && (l.includes('catalog') || l.includes('model')))
        return false
      if (l.includes('nu înlocuiesc consultul medical')) return false
      if (l.includes('valorile per 100 g provin') && l.includes('orientativ')) return false
      return true
    })
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function renderInlineBold(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold text-zinc-50">
          {part.slice(2, -2)}
        </strong>
      )
    }
    return <span key={i}>{part}</span>
  })
}

/** Împarte rezumatul: intro, contribuții, acoperire — pe linii separate când e posibil. */
function splitReadableChunks(text: string): string[] {
  const t = text.trim()
  if (!t) return []

  const markerRes = [/Contribuții nutriționale dominante:/i, /Acoperirea globală estimată/i]
  const hitIdx = markerRes
    .map((re) => t.search(re))
    .filter((idx) => idx >= 0)
    .sort((a, b) => a - b)
  const uniqueHits = hitIdx.filter((idx, i) => i === 0 || idx !== hitIdx[i - 1])

  if (uniqueHits.length > 0) {
    const chunks: string[] = []
    let pos = 0
    for (const idx of uniqueHits) {
      if (idx > pos) {
        const slice = t.slice(pos, idx).trim()
        if (slice && !isSeparatorOnlyChunk(slice)) chunks.push(slice)
      }
      pos = idx
    }
    const tail = t.slice(pos).trim()
    if (tail && !isSeparatorOnlyChunk(tail)) chunks.push(tail)
    if (chunks.length >= 2) return chunks
  }

  const byNewline = t
    .split(/\n+/)
    .map((line) => line.replace(/[ \t]+/g, ' ').trim())
    .filter((line) => line && !isSeparatorOnlyChunk(line))
  if (byNewline.length >= 2) return byNewline

  const bySemi = t.split(/;\s+/).map((s) => s.trim()).filter((s) => s && !isSeparatorOnlyChunk(s))
  if (bySemi.length >= 2) return bySemi

  const sentences = t
    .split(/(?<=[.!?])\s+(?=[A-ZĂÂÎȘȚ])/u)
    .map((s) => s.trim())
    .filter((s) => s && !isSeparatorOnlyChunk(s))
  if (sentences.length >= 2) return sentences

  return [t]
}

function ReadableParagraphs({ text }: { text: string }) {
  const chunks = splitReadableChunks(text)
  if (chunks.length <= 1) {
    return (
      <p className="text-zinc-200 text-base sm:text-sm leading-relaxed break-words whitespace-pre-line">
        {renderInlineBold(chunks[0] ?? '')}
      </p>
    )
  }
  return (
    <ul className="space-y-2.5 list-none pl-0 m-0">
      {chunks.map((chunk, idx) => (
        <li key={idx} className="flex gap-2.5 text-zinc-200 text-base sm:text-sm leading-relaxed break-words">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent/90" aria-hidden />
          <span className="min-w-0">{renderInlineBold(chunk)}</span>
        </li>
      ))}
    </ul>
  )
}

function ExplanationSections({ rawText }: { rawText: string }) {
  const { t } = useTranslation()
  const normalized = stripMedicalDisclaimersFromExplanation(normalizeExplanationRaw(rawText))
  const parts = splitExplanationSections(normalized)
  if (parts.length <= 1) {
    return <ReadableParagraphs text={parts[0] ?? normalized} />
  }
  const first = parts[0] ?? ''
  const last = parts[parts.length - 1]
  const middleText = parts
    .slice(1, -1)
    .join('\n\n')
    .trim()

  if (parts.length === 2) {
    return (
      <div className="space-y-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-accent/85 mb-1.5">{t('recommendations.card.summary')}</p>
          <div className="text-zinc-200 text-base sm:text-sm leading-relaxed break-words">
            <ReadableParagraphs text={first} />
          </div>
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-accent/85 mb-1.5">
            {t('recommendations.card.nutrientDetail')}
          </p>
          <div className="text-zinc-200 text-base sm:text-sm leading-relaxed break-words">
            <ReadableParagraphs text={last} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-accent/85 mb-1.5">{t('recommendations.card.summary')}</p>
        <div className="text-zinc-200 text-base sm:text-sm leading-relaxed break-words">
          <ReadableParagraphs text={first} />
        </div>
      </div>
      {middleText ? (
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-accent/85 mb-1.5">
            {t('recommendations.card.nutrientDetail')}
          </p>
          <div className="text-zinc-200 text-base sm:text-sm leading-relaxed break-words">
            <ReadableParagraphs text={middleText} />
          </div>
        </div>
      ) : null}
      {parts.length >= 2 ? (
        <div className="rounded-lg border border-line bg-white/[0.02] px-3 py-2.5">
          <div className="text-xs text-zinc-400 leading-relaxed break-words">
            <ReadableParagraphs text={last} />
          </div>
        </div>
      ) : null}
    </div>
  )
}

interface RecommendationCardProps {
  recommendation: {
    food_id: number
    food: {
      id: number
      name: string
      category: string
      calories?: number
    }
    score: number
    coverage: number
    explanation: {
      text: string
      portion: number
      portion_unit?: 'g' | 'ml' | string
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
  userId?: number
  onFeedbackSent?: (recId: number, rating: number | null, newLikes: number, newDislikes: number) => void
  onReplaceRequested?: (recId: number) => Promise<void>
}

const RecommendationCard = ({
  recommendation,
  userId,
  onFeedbackSent,
  onReplaceRequested,
}: RecommendationCardProps) => {
  const { t } = useTranslation()
  const { food, explanation, coverage, feedback } = recommendation
  const portionKcal = estimatePortionCalories(recommendation)
  const [feedbackStatus, setFeedbackStatus] = useState<'idle' | 'sent' | 'error'>('idle')
  const [feedbackError, setFeedbackError] = useState<string | null>(null)
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false)
  const [myRating, setMyRating] = useState<number | undefined | null>(recommendation.my_rating)
  const [localCounts, setLocalCounts] = useState(feedback ? { ...feedback } : { likes: 0, dislikes: 0 })
  const [showDislikeModal, setShowDislikeModal] = useState(false)
  const [replaceLoading, setReplaceLoading] = useState(false)

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
                  <h3 className="text-lg sm:text-xl font-semibold tracking-tight text-zinc-50 break-words">{food.name}</h3>
                  <span className="flex-shrink-0 rounded-md border border-accent-border bg-accent-soft px-2.5 py-0.5 text-xs font-medium text-accent">
                    {formatFoodCategory(food.category)}
                  </span>
                </div>
                <p className="text-base sm:text-sm text-zinc-300 mb-3 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span>
                    {t('recommendations.card.portion')}{' '}
                    <strong className="text-accent">
                      {formatPortionSuggestion(explanation.portion, explanation.portion_unit, food.category)}
                    </strong>
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
                <div className="flex items-center gap-2 mb-4 min-w-0">
                  <div className="flex-1 min-w-0 bg-white/10 rounded-full h-3 sm:h-2.5 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(coverage, 100)}%` }}
                      transition={{ duration: 0.22, ease: 'easeOut' }}
                      className="bg-accent h-3 sm:h-2.5 rounded-full"
                    />
                  </div>
                  <span className="text-base sm:text-sm font-semibold text-accent min-w-[56px] text-right tabular-nums">
                    {coverage.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="mb-5 rounded-lg border border-line bg-white/[0.03] p-4">
              <ExplanationSections rawText={explanation.text} />
            </div>

            {explanation.reasons && explanation.reasons.length > 0 && (
              <div className="mb-4 space-y-2">
                <p className="text-base sm:text-sm font-semibold text-accent mb-3 flex items-center gap-2">
                  <CheckCircle2 aria-hidden="true" className="w-4 h-4 flex-shrink-0" />
                  {t('recommendations.card.whyTitle')}
                </p>
                <ul className="space-y-2">
                  {explanation.reasons.map((reason, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-base sm:text-sm text-zinc-300 leading-relaxed break-words"
                    >
                      <CheckCircle2 className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" />
                      <span className="leading-relaxed whitespace-pre-line">{faraPrefixContext(reason)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.tips && explanation.tips.length > 0 && (
              <div className="mt-4 pt-4 border-t border-line">
                <p className="text-base sm:text-sm font-semibold text-zinc-200 mb-2 flex items-center gap-2">
                  <Info aria-hidden="true" className="w-4 h-4 flex-shrink-0 text-accent" />
                  {t('recommendations.card.tipsTitle')}
                </p>
                <ul className="space-y-2">
                  {explanation.tips.map((tip, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-base sm:text-sm text-zinc-300 bg-white/[0.03] border border-line p-3 rounded-lg break-words">
                      <Lightbulb aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
                      <span>{faraPrefixContext(tip)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {explanation.alternatives && explanation.alternatives.length > 0 && (
              <div className="mt-4 pt-4 border-t border-line">
                <p className="text-base sm:text-sm font-semibold text-zinc-200 mb-2">{t('recommendations.card.alternatives')}</p>
                <p className="text-base sm:text-sm text-zinc-300 break-words">{explanation.alternatives.join(', ')}</p>
              </div>
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

export default RecommendationCard
