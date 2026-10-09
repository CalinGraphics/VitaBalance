import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { BookHeart, ChevronDown, Pencil, Scale, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { CheckIn } from '../../services/api'
import { ENERGY_COLORS } from './progressStats'

// În coloana îngustă de lângă formular încap cam patru zile; restul se deschid la cerere.
const PREVIEW = 4

interface JournalTimelineProps {
  checkins: CheckIn[]
  selectedDay: string
  locale: string
  onEdit: (day: string) => void
  onDelete: (id: number) => void
}

/** Jurnalul ca o cronologie: punctul fiecărei zile are culoarea energiei, iar zilele șterse ies animat. */
const JournalTimeline = ({ checkins, selectedDay, locale, onEdit, onDelete }: JournalTimelineProps) => {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? checkins : checkins.slice(0, PREVIEW)
  // Ziua săptămânii cu majusculă, luna rămâne cu literă mică (în română lunile nu se scriu cu majusculă).
  const dayTitle = (iso: string) => {
    const s = new Date(`${iso}T00:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' })
    return s.charAt(0).toUpperCase() + s.slice(1)
  }
  return (
    <div>
      <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-zinc-50">
        <BookHeart aria-hidden="true" className="h-4 w-4 text-accent" />
        {t('progress.history.title')}
      </h3>
      {checkins.length === 0 ? (
        <p className="text-sm text-zinc-400">{t('progress.history.empty')}</p>
      ) : (
        <ol className="relative space-y-3 before:absolute before:bottom-3 before:left-[11px] before:top-3 before:w-px before:bg-gradient-to-b before:from-accent/50 before:via-line-strong before:to-transparent">
          <AnimatePresence initial={false}>
            {visible.map((c, i) => {
              const color = c.energy != null ? ENERGY_COLORS[c.energy - 1] : '#52525b'
              return (
                <motion.li
                  key={c.id}
                  layout
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 24, height: 0, marginTop: 0 }}
                  transition={{ duration: 0.35, delay: Math.min(i, 8) * 0.04 }}
                  className="relative pl-9"
                >
                  <span aria-hidden="true" className="absolute left-[5px] top-4 h-[13px] w-[13px] rounded-full border-2 border-surface"
                    style={{ backgroundColor: color, boxShadow: `0 0 0 3px ${color}26, 0 0 12px ${color}66` }} />
                  <div className={`flex items-start justify-between gap-3 rounded-xl border p-3.5 transition-colors ${
                    c.checked_on === selectedDay ? 'border-accent-border bg-accent-soft' : 'border-line bg-white/[0.02] hover:border-line-strong'
                  }`}>
                    <div className="min-w-0 space-y-1.5 text-sm text-zinc-300">
                      <p className="font-semibold text-zinc-100">{dayTitle(c.checked_on)}</p>
                      {c.symptoms.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {c.symptoms.map((s) => (
                            <span key={s} className="rounded-full border border-amber-400/25 bg-amber-400/[0.08] px-2 py-0.5 text-[11px] font-medium text-amber-200">
                              {t(`progress.symptom.${s}`)}
                            </span>
                          ))}
                          {c.severity && (
                            <span className="rounded-full border border-line-strong px-2 py-0.5 text-[11px] text-zinc-400">
                              {t(`progress.severity.${c.severity}`)}
                            </span>
                          )}
                        </div>
                      )}
                      {(c.energy != null || c.weight != null) && (
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-400">
                          {c.energy != null && (
                            <span className="flex items-center gap-2">
                              <span aria-hidden="true" className="flex gap-0.5">
                                {[1, 2, 3, 4, 5].map((n) => (
                                  <span key={n} className="h-2.5 w-1.5 rounded-sm" style={{ backgroundColor: n <= c.energy! ? color : 'rgba(255,255,255,0.08)' }} />
                                ))}
                              </span>
                              {t('progress.history.energy', { value: c.energy })}
                            </span>
                          )}
                          {c.weight != null && (
                            <span className="flex items-center gap-1.5">
                              <Scale aria-hidden="true" className="h-3.5 w-3.5" />
                              {t('progress.history.weight', { value: c.weight })}
                            </span>
                          )}
                        </div>
                      )}
                      {c.notes && <p className="break-words text-xs italic text-zinc-400">“{c.notes}”</p>}
                    </div>
                    <div className="flex flex-shrink-0 gap-1">
                      <button type="button" onClick={() => onEdit(c.checked_on)} aria-label={t('progress.history.edit')} title={t('progress.history.edit')}
                        className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-accent-soft hover:text-accent">
                        <Pencil aria-hidden="true" className="h-4 w-4" />
                      </button>
                      <button type="button" onClick={() => onDelete(c.id)} aria-label={t('progress.history.delete')} title={t('progress.history.delete')}
                        className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-red-500/10 hover:text-red-300">
                        <Trash2 aria-hidden="true" className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </motion.li>
              )
            })}
          </AnimatePresence>
        </ol>
      )}
      {checkins.length > PREVIEW && (
        <button type="button" onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}
          className="mt-4 inline-flex min-h-[40px] cursor-pointer items-center gap-1.5 rounded-lg border border-line-strong px-3 text-sm font-medium text-zinc-300 transition-colors hover:border-accent-border hover:text-accent">
          {expanded ? t('progress.history.showLess') : t('progress.history.showMore', { count: checkins.length })}
          <ChevronDown aria-hidden="true" className={`h-4 w-4 transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} />
        </button>
      )}
    </div>
  )
}

export default JournalTimeline
