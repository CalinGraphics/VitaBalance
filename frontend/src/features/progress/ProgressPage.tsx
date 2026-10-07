import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Activity, Stethoscope, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Alert, GlassCard, InputField, PageHeader, PrimaryButton, Spinner } from '../../shared/components'
import { progressService, type ProgressData } from '../../services/api'
import type { User } from '../../shared/types'
import { ChartSkeleton } from '../recommendations/components/RecommendationSkeleton'

const ProgressCharts = lazy(() => import('./ProgressCharts'))

const today = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

interface ProgressPageProps {
  user: User
  /** O zi salvată/ștearsă schimbă stările recente, deci și recomandările. */
  onCheckinChange?: () => void
}

const chip = (active: boolean) =>
  `min-h-[36px] cursor-pointer rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
    active
      ? 'border-accent-border bg-accent-soft text-accent'
      : 'border-line-strong bg-white/[0.03] text-zinc-300 hover:border-accent-border hover:text-accent'
  }`

const ProgressPage = ({ user, onCheckinChange }: ProgressPageProps) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language === 'en' ? 'en' : 'ro'
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
    prefill(data, value)
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

  const insights = data?.insights
  const symptomList = useMemo(
    () => (insights?.recent_symptoms ?? []).map((s) => t(`progress.symptom.${s}`).toLowerCase()),
    [insights, t]
  )
  const listFormat = (items: string[]) =>
    new Intl.ListFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { style: 'long', type: 'conjunction' }).format(items)

  if (!data && !loadError) {
    return (
      <GlassCard className="w-full max-w-5xl py-12 text-center">
        <Spinner className="mb-3 h-7 w-7 text-accent" />
        <p className="text-zinc-300">{t('common.loading')}</p>
      </GlassCard>
    )
  }

  return (
    <div className="w-full max-w-5xl space-y-6">
      <GlassCard className="w-full !max-w-none">
        <PageHeader Icon={Activity} title={t('progress.title')} subtitle={t('progress.subtitle')} />
        {loadError && <Alert variant="error">{t('progress.loadError')}</Alert>}
        {data && !data.storage_available && <Alert variant="warning" className="mb-4">{t('progress.unavailable')}</Alert>}

        {data?.storage_available && (
          <div className="space-y-5">
            <h3 className="text-base font-semibold text-zinc-50">{t('progress.checkin.title')}</h3>
            <InputField label={t('progress.checkin.date')} type="date" value={day} max={today()}
              onChange={(e) => changeDay(e.target.value || today())} />

            <div>
              <p className="mb-2 text-sm font-medium text-zinc-200">{t('progress.checkin.symptoms')}</p>
              <div className="flex flex-wrap gap-2">
                {data.symptom_codes.map((code) => (
                  <button key={code} type="button" aria-pressed={symptoms.includes(code)} onClick={() => toggle(code)}
                    className={chip(symptoms.includes(code))}>
                    {t(`progress.symptom.${code}`)}
                  </button>
                ))}
              </div>
            </div>

            {symptoms.length > 0 && (
              <div>
                <p className="mb-2 text-sm font-medium text-zinc-200">{t('progress.checkin.severity')}</p>
                <div className="flex flex-wrap gap-2">
                  {[1, 2, 3].map((s) => (
                    <button key={s} type="button" aria-pressed={severity === s} onClick={() => setSeverity(s)} className={chip(severity === s)}>
                      {t(`progress.severity.${s}`)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <p className="mb-1 text-sm font-medium text-zinc-200">{t('progress.checkin.energy')}</p>
              <p className="mb-2 text-xs text-zinc-400">{t('progress.checkin.energyHint')}</p>
              <div className="flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5].map((e) => (
                  <button key={e} type="button" aria-pressed={energy === e} onClick={() => setEnergy(energy === e ? null : e)}
                    className={`${chip(energy === e)} min-w-[44px]`}>
                    {e}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <InputField label={t('progress.checkin.weight')} type="text" inputMode="decimal" value={weight}
                onChange={(e) => setWeight(e.target.value)} placeholder={user.weight ? String(user.weight) : undefined} />
            </div>
            <InputField label={t('progress.checkin.notes')} value={notes} textarea rows={3}
              onChange={(e) => setNotes(e.target.value.slice(0, 1000))} placeholder={t('progress.checkin.notesPlaceholder')} />

            {status && <Alert variant={status.kind}>{status.text}</Alert>}
            <PrimaryButton onClick={save} disabled={saving}>
              {saving ? t('progress.checkin.saving') : t('progress.checkin.save')}
            </PrimaryButton>
          </div>
        )}
      </GlassCard>

      {insights && (
        <GlassCard className="w-full !max-w-none">
          <h3 className="mb-3 text-base font-semibold text-zinc-50">{t('progress.insights.title')}</h3>
          <div className="space-y-3 text-sm text-zinc-300">
            <p>{symptomList.length ? t('progress.insights.recent', { list: listFormat(symptomList) }) : t('progress.insights.none')}</p>
            {insights.adjustments.length > 0 && (
              <div>
                <p className="font-medium text-zinc-200">{t('progress.insights.adjusted')}</p>
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {insights.adjustments.map((id) => <li key={id}>{t(`progress.adjustment.${id}`)}</li>)}
                </ul>
              </div>
            )}
            {insights.lab_suggestions.length > 0 && (
              <p>{t('progress.insights.labs', { list: listFormat(insights.lab_suggestions.map((m) => t(`labs.names.${m}`))) })}</p>
            )}
            {insights.see_doctor && (
              <div role="note" className="rounded-lg border border-amber-400/30 bg-amber-400/[0.06] p-3 text-amber-100">
                <p className="mb-1 flex items-center gap-2 font-semibold">
                  <Stethoscope aria-hidden="true" className="h-4 w-4" />
                  {t('progress.insights.doctor')}
                </p>
                <ul className="list-disc space-y-1 pl-5">
                  {insights.see_doctor_reasons.map((r) => <li key={r}>{t(`progress.insights.doctorReason.${r}`)}</li>)}
                </ul>
              </div>
            )}
            <p className="text-xs text-zinc-500">{t('progress.insights.disclaimer')}</p>
          </div>
        </GlassCard>
      )}

      {data && (
        <GlassCard className="w-full !max-w-none">
          <Suspense fallback={<ChartSkeleton />}>
            <ProgressCharts series={data.series} />
          </Suspense>
        </GlassCard>
      )}

      {data?.storage_available && (
        <GlassCard className="w-full !max-w-none">
          <h3 className="mb-3 text-base font-semibold text-zinc-50">{t('progress.history.title')}</h3>
          {data.checkins.length === 0 ? (
            <p className="text-sm text-zinc-400">{t('progress.history.empty')}</p>
          ) : (
            <ul className="divide-y divide-line">
              {data.checkins.map((c) => (
                <li key={c.id} className="flex items-start justify-between gap-3 py-3">
                  <div className="min-w-0 text-sm text-zinc-300">
                    <p className="font-semibold text-zinc-100">
                      {new Date(`${c.checked_on}T00:00:00`).toLocaleDateString(lang === 'en' ? 'en-GB' : 'ro-RO', { weekday: 'short', day: 'numeric', month: 'long' })}
                    </p>
                    {c.symptoms.length > 0 && (
                      <p>
                        {listFormat(c.symptoms.map((s) => t(`progress.symptom.${s}`).toLowerCase()))}
                        {c.severity ? ` · ${t(`progress.severity.${c.severity}`).toLowerCase()}` : ''}
                      </p>
                    )}
                    <p className="text-xs text-zinc-400">
                      {[c.energy != null ? t('progress.history.energy', { value: c.energy }) : null,
                        c.weight != null ? t('progress.history.weight', { value: c.weight }) : null].filter(Boolean).join(' · ')}
                    </p>
                    {c.notes && <p className="mt-1 break-words text-xs text-zinc-400">{c.notes}</p>}
                  </div>
                  <button type="button" onClick={() => void remove(c.id)} aria-label={t('progress.history.delete')}
                    title={t('progress.history.delete')}
                    className="flex h-9 w-9 flex-shrink-0 cursor-pointer items-center justify-center rounded-lg text-zinc-400 transition-colors hover:bg-red-500/10 hover:text-red-300">
                    <Trash2 aria-hidden="true" className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </GlassCard>
      )}
    </div>
  )
}

export default ProgressPage
