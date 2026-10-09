import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, PenLine } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Alert, GlassCard, InputField, PrimaryButton, Spinner } from '../../shared/components'
import { progressService, type ProgressData } from '../../services/api'
import type { User } from '../../shared/types'
import { ChartSkeleton } from '../recommendations/components/RecommendationSkeleton'
import InsightsPanel from './InsightsPanel'
import JournalTimeline from './JournalTimeline'
import ProgressHero from './ProgressHero'
import { ENERGY_COLORS, summarize, today } from './progressStats'

const ProgressCharts = lazy(() => import('./ProgressCharts'))

interface ProgressPageProps {
  user: User
  /** O zi salvată/ștearsă schimbă stările recente, deci și recomandările. */
  onCheckinChange?: () => void
}

const chip = (active: boolean) =>
  `inline-flex min-h-[36px] cursor-pointer items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
    active
      ? 'border-accent-border bg-accent-soft text-accent'
      : 'border-line-strong bg-white/[0.03] text-zinc-300 hover:border-accent-border hover:text-accent'
  }`

const SectionLabel = ({ children, hint }: { children: string; hint?: string }) => (
  <div className="mb-2">
    <p className="text-sm font-medium text-zinc-200">{children}</p>
    {hint && <p className="mt-0.5 text-xs text-zinc-500">{hint}</p>}
  </div>
)

const ProgressPage = ({ user, onCheckinChange }: ProgressPageProps) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language === 'en' ? 'en' : 'ro'
  const locale = lang === 'en' ? 'en-GB' : 'ro-RO'
  const [data, setData] = useState<ProgressData | null>(null)
  const [loadError, setLoadError] = useState(false)
  const [day, setDay] = useState(today())
  const [symptoms, setSymptoms] = useState<string[]>([])
  const [severity, setSeverity] = useState<number>(1)
  const [energy, setEnergy] = useState<number | null>(null)
  const [weight, setWeight] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<{ kind: 'success' | 'error' | 'warning'; text: string } | null>(null)

  const dayRef = useRef(day)
  const formRef = useRef<HTMLDivElement>(null)

  // Ziua aleasă se precompletează din jurnal (un rând pe zi: salvarea o actualizează). Se apelează explicit la
  // încărcare și la schimbarea zilei, nu dintr-un efect: un efect întârziat ar putea șterge o alegere deja făcută.
  const prefill = useCallback((source: ProgressData | null, forDay: string) => {
    const existing = source?.checkins.find((c) => c.checked_on === forDay)
    setSymptoms(existing?.symptoms ?? [])
    setSeverity(existing?.severity ?? 1)
    setEnergy(existing?.energy ?? null)
    setWeight(existing?.weight != null ? String(existing.weight) : '')
    setNotes(existing?.notes ?? '')
  }, [])

  const load = useCallback(async () => {
    if (!user.id) return
    try {
      const fresh = await progressService.get(user.id)
      setData(fresh)
      setLoadError(false)
      prefill(fresh, dayRef.current)
    } catch {
      setLoadError(true)
    }
  }, [user.id, prefill])

  useEffect(() => {
    void load()
  }, [load])

  const changeDay = (value: string) => {
    dayRef.current = value
    setDay(value)
    setStatus(null)
    prefill(data, value)
  }

  const editDay = (value: string) => {
    changeDay(value)
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const toggle = (code: string) =>
    setSymptoms((prev) => (prev.includes(code) ? prev.filter((s) => s !== code) : [...prev, code]))

  const save = async () => {
    if (!user.id) return
    const w = weight.trim() ? Number(weight.replace(',', '.')) : null
    if (!symptoms.length && energy == null && w == null && !notes.trim()) {
      setStatus({ kind: 'warning', text: t('progress.checkin.empty') })
      return
    }
    setSaving(true)
    setStatus(null)
    try {
      await progressService.saveCheckin({
        user_id: user.id,
        checked_on: day,
        symptoms,
        severity: symptoms.length ? severity : null,
        energy,
        weight: w != null && Number.isFinite(w) ? w : null,
        notes: notes.trim() || null,
      })
      setStatus({ kind: 'success', text: t('progress.checkin.saved') })
      onCheckinChange?.()
      await load()
    } catch (err: unknown) {
      const code = (err as { response?: { status?: number } })?.response?.status
      setStatus({ kind: 'error', text: code === 503 ? t('progress.unavailable') : t('progress.checkin.error') })
    } finally {
      setSaving(false)
    }
  }

  const remove = async (id: number) => {
    if (!user.id) return
    try {
      await progressService.deleteCheckin(user.id, id)
      onCheckinChange?.()
      await load()
    } catch {
      setStatus({ kind: 'error', text: t('progress.checkin.error') })
    }
  }

  const recentDays = data?.recent_days ?? 14
  const summary = useMemo(() => (data ? summarize(data, recentDays) : null), [data, recentDays])
  const listFormat = (items: string[]) =>
    new Intl.ListFormat(locale, { style: 'long', type: 'conjunction' }).format(items)
  const existing = data?.checkins.some((c) => c.checked_on === day) ?? false

  if (!data && !loadError) {
    return (
      <div role="status" aria-busy="true" className="w-full max-w-5xl space-y-6">
        <div className="relative overflow-hidden rounded-card border border-line bg-surface p-8">
          <div className="mb-6 flex items-center gap-3.5">
            <Spinner className="h-7 w-7 text-accent" />
            <p className="text-zinc-300">{t('common.loading')}</p>
          </div>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-28 animate-pulse rounded-xl bg-white/[0.05]" />)}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-5xl space-y-6">
      {data && summary && (
        <ProgressHero summary={summary} checkins={data.checkins} days={recentDays} selectedDay={day}
          onSelectDay={changeDay} showStrip={data.storage_available} />
      )}
      {loadError && <Alert variant="error">{t('progress.loadError')}</Alert>}
      {data && !data.storage_available && <Alert variant="warning">{t('progress.unavailable')}</Alert>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {data?.storage_available && (
          <div ref={formRef} className="scroll-mt-24 lg:col-span-3">
            <GlassCard className="h-full !max-w-none">
              <div className="space-y-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-50">
                      <PenLine aria-hidden="true" className="h-4 w-4 text-accent" />
                      {t('progress.checkin.title')}
                    </h3>
                    <AnimatePresence mode="wait" initial={false}>
                      <motion.p key={day} initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                        className="mt-0.5 text-xs text-zinc-500">
                        {existing
                          ? t('progress.checkin.editing')
                          : t('progress.checkin.forDay', { date: new Date(`${day}T00:00:00`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' }) })}
                      </motion.p>
                    </AnimatePresence>
                  </div>
                  <div className="w-full sm:w-44">
                    <InputField label={t('progress.checkin.date')} type="date" value={day} max={today()}
                      onChange={(e) => changeDay(e.target.value || today())} />
                  </div>
                </div>

                <div>
                  <SectionLabel>{t('progress.checkin.symptoms')}</SectionLabel>
                  <div className="flex flex-wrap gap-2">
                    {data.symptom_codes.map((code) => {
                      const on = symptoms.includes(code)
                      return (
                        <motion.button key={code} type="button" aria-pressed={on} onClick={() => toggle(code)}
                          whileTap={{ scale: 0.94 }} layout="position" className={chip(on)}>
                          <AnimatePresence initial={false}>
                            {on && (
                              <motion.span initial={{ width: 0, opacity: 0 }} animate={{ width: 'auto', opacity: 1 }} exit={{ width: 0, opacity: 0 }}
                                className="inline-flex overflow-hidden" aria-hidden="true">
                                <Check className="h-3.5 w-3.5" />
                              </motion.span>
                            )}
                          </AnimatePresence>
                          {t(`progress.symptom.${code}`)}
                        </motion.button>
                      )
                    })}
                  </div>
                </div>

                <AnimatePresence initial={false}>
                  {symptoms.length > 0 && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden">
                      <SectionLabel>{t('progress.checkin.severity')}</SectionLabel>
                      <div className="inline-flex rounded-full border border-line-strong bg-white/[0.03] p-1">
                        {[1, 2, 3].map((s) => (
                          <button key={s} type="button" aria-pressed={severity === s} onClick={() => setSeverity(s)}
                            className={`relative min-h-[36px] cursor-pointer rounded-full px-4 text-xs font-medium transition-colors ${
                              severity === s ? (s === 3 ? 'text-amber-950' : 'text-accent-fg') : 'text-zinc-300 hover:text-zinc-50'
                            }`}>
                            {severity === s && (
                              <motion.span layoutId="severity-pill" aria-hidden="true"
                                className={`absolute inset-0 rounded-full ${s === 3 ? 'bg-amber-400' : s === 2 ? 'bg-accent-hover' : 'bg-accent'}`}
                                transition={{ type: 'spring', stiffness: 420, damping: 34 }} />
                            )}
                            <span className="relative">{t(`progress.severity.${s}`)}</span>
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <div>
                  <SectionLabel hint={t('progress.checkin.energyHint')}>{t('progress.checkin.energy')}</SectionLabel>
                  <div className="flex items-end gap-2">
                    {[1, 2, 3, 4, 5].map((e) => {
                      const on = energy != null && e <= energy
                      const color = ENERGY_COLORS[(energy ?? e) - 1]
                      return (
                        <motion.button key={e} type="button" aria-pressed={energy === e} onClick={() => setEnergy(energy === e ? null : e)}
                          whileHover={{ y: -2 }} whileTap={{ scale: 0.92 }}
                          className={`group flex min-w-[48px] flex-1 cursor-pointer flex-col items-center gap-1.5 rounded-lg border px-1 pb-2 pt-2 transition-colors sm:flex-none ${
                            energy === e ? 'border-accent-border bg-white/[0.04]' : 'border-line hover:border-line-strong'
                          }`}>
                          <span aria-hidden="true" className="flex h-12 w-5 items-end overflow-hidden rounded bg-white/[0.06]">
                            <motion.span className="block w-full rounded"
                              initial={false}
                              animate={{ height: `${e * 20}%`, backgroundColor: on ? color : 'rgba(255,255,255,0.14)', boxShadow: on ? `0 0 12px ${color}88` : '0 0 0 transparent' }}
                              transition={{ type: 'spring', stiffness: 300, damping: 24, delay: on ? (e - 1) * 0.04 : 0 }} />
                          </span>
                          <span className={`text-xs font-semibold tabular-nums ${energy === e ? 'text-zinc-50' : 'text-zinc-400'}`}>{e}</span>
                        </motion.button>
                      )
                    })}
                    <AnimatePresence mode="wait">
                      {energy != null && (
                        <motion.span key={energy} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
                          className="ml-2 hidden self-center text-sm font-medium sm:inline" style={{ color: ENERGY_COLORS[energy - 1] }}>
                          {t(`progress.energyLevel.${energy}`)}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <InputField label={t('progress.checkin.weight')} type="text" inputMode="decimal" value={weight}
                    onChange={(e) => setWeight(e.target.value)} placeholder={user.weight ? String(user.weight) : undefined} />
                  <div className="sm:col-span-2">
                    <InputField label={t('progress.checkin.notes')} value={notes} textarea rows={2}
                      onChange={(e) => setNotes(e.target.value.slice(0, 1000))} placeholder={t('progress.checkin.notesPlaceholder')} />
                  </div>
                </div>

                <AnimatePresence>
                  {status && (
                    <motion.div key={status.text} initial={{ opacity: 0, y: 6, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0 }}>
                      <Alert variant={status.kind}>{status.text}</Alert>
                    </motion.div>
                  )}
                </AnimatePresence>
                <PrimaryButton onClick={save} disabled={saving}>
                  {saving ? <Spinner className="h-4 w-4" /> : <Check aria-hidden="true" className="h-4 w-4" />}
                  {saving ? t('progress.checkin.saving') : t('progress.checkin.save')}
                </PrimaryButton>
              </div>
            </GlassCard>
          </div>
        )}

        {/* Coloana din dreapta: concluziile, apoi jurnalul, ca spațiul de lângă formular să nu rămână gol. */}
        {(data?.insights || data?.storage_available) && (
          <div className={`space-y-6 ${data?.storage_available ? 'lg:col-span-2' : 'lg:col-span-5'}`}>
            {data?.insights && (
              <GlassCard className="!max-w-none">
                <InsightsPanel insights={data.insights} listFormat={listFormat} />
              </GlassCard>
            )}
            {data?.storage_available && (
              <GlassCard className="!max-w-none">
                <JournalTimeline checkins={data.checkins} selectedDay={day} locale={locale} onEdit={editDay} onDelete={(id) => void remove(id)} />
              </GlassCard>
            )}
          </div>
        )}
      </div>

      {data && (
        <GlassCard className="w-full !max-w-none">
          <Suspense fallback={<ChartSkeleton />}>
            <ProgressCharts series={data.series} />
          </Suspense>
        </GlassCard>
      )}
    </div>
  )
}

export default ProgressPage
