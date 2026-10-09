import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FlaskConical, ArrowRight, SkipForward, FileUp, ArrowLeft, Trash2, Droplet, Sun, Gem, Info, Check, Plus, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, HeroBackdrop, InputField, PrimaryButton, Alert, Spinner } from '../../../shared/components'
import LabField from '../components/LabField'
import { labResultsService, type LabResultsCreatePayload } from '../../../services/api'
import { regenerateRecommendationsAfterSave } from '../../recommendations/utils/regenerateAfterSave'
import {
  LAB_KEYS,
  coerceLabNumeric,
  extractLabValuesFromTextLocal,
  normalizeLabNoteText,
  type LabKey,
} from '../utils/labLocalExtract'
import { extractTextFromPdfFile } from '../../../shared/utils/pdfTextExtractor'
import { parseOptionalDecimal, sanitizeDecimalInput } from '../../../shared/utils/numberParsing'
import type { User } from '../../../shared/types'

interface MedicalLabResultsPageProps {
  user: User
  onComplete: () => void
  onBackToDashboard?: () => void
}

type LabInputs = Record<LabKey, string> & { notes: string }

type LabResult = { user_id: number; notes?: string } & Partial<Record<LabKey, number | null>>

/**
 * Unitatea și intervalul orientativ pentru fiecare analiză; numele vine din i18n (`labs.names.<cheie>`).
 * `range` e textul din câmpul gol, `low`/`high` dau starea afișată sub câmp (doar orientativ, nu un diagnostic).
 */
const LAB_FIELDS: Record<LabKey, { unit: string; range?: string; low?: number; high?: number }> = {
  hemoglobin: { unit: 'g/dL', range: '12-16 g/dL', low: 12, high: 16 },
  ferritin: { unit: 'ng/mL', range: '15-150 ng/mL', low: 15, high: 150 },
  vitamin_d: { unit: 'ng/mL', range: '30-100 ng/mL', low: 30, high: 100 },
  vitamin_b12: { unit: 'pg/mL', range: '200-900 pg/mL', low: 200, high: 900 },
  calcium: { unit: 'mg/dL', range: '8.5-10.5 mg/dL', low: 8.5, high: 10.5 },
  magnesium: { unit: 'mg/dL', range: '1.7-2.2 mg/dL', low: 1.7, high: 2.2 },
  zinc: { unit: 'mcg/dL', range: '70-100 mcg/dL', low: 70, high: 100 },
  protein: { unit: 'g/dL', range: '6.0-8.0 g/dL', low: 6, high: 8 },
  folate: { unit: 'ng/mL', range: '> 3 ng/mL', low: 3 },
  vitamin_a: { unit: 'μg/dL', range: '> 20 μg/dL', low: 20 },
  vitamin_c: { unit: 'μmol/L', low: 23, high: 85 },
  iodine: { unit: 'μg/L', range: '> 100 μg/L', low: 100 },
  vitamin_k: { unit: 'ng/mL' },
  potassium: { unit: 'mmol/L', range: '> 3.5 mmol/L', low: 3.5 },
}

/** Analizele pe grupe, ca formularul lung să se parcurgă ușor. */
const LAB_GROUPS: { key: 'blood' | 'vitamins' | 'minerals'; Icon: LucideIcon; fields: LabKey[] }[] = [
  { key: 'blood', Icon: Droplet, fields: ['hemoglobin', 'ferritin', 'protein'] },
  { key: 'vitamins', Icon: Sun, fields: ['vitamin_d', 'vitamin_b12', 'folate', 'vitamin_a', 'vitamin_c', 'vitamin_k'] },
  { key: 'minerals', Icon: Gem, fields: ['calcium', 'magnesium', 'zinc', 'iodine', 'potassium'] },
]

/** Inel de completare: câte analize au o valoare. */
function CompletionRing({ count, total, label }: { count: number; total: number; label: string }) {
  const r = 26
  const c = 2 * Math.PI * r
  const ratio = total ? count / total : 0
  return (
    <div className="flex items-center gap-3" role="img" aria-label={label}>
      <svg viewBox="0 0 64 64" className="h-14 w-14 -rotate-90" aria-hidden="true">
        <defs>
          <linearGradient id="lab-ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#5eead4" />
            <stop offset="100%" stopColor="#14b8a6" />
          </linearGradient>
        </defs>
        <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
        <motion.circle
          cx="32"
          cy="32"
          r={r}
          fill="none"
          stroke="url(#lab-ring)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - ratio) }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
        />
      </svg>
      <p aria-hidden="true" className="text-2xl font-semibold tabular-nums leading-none text-zinc-50">
        {count}
        <span className="text-sm font-normal text-zinc-500">/{total}</span>
      </p>
    </div>
  )
}

/**
 * Sugestii pentru câmpul de observații. `note` este textul CANONIC în română care se salvează în baza de date:
 * backend-ul îl interpretează prin cuvinte-cheie românești (deficit_calculator / clinical_context), deci
 * trebuie inserat identic indiferent de limba interfeței. Doar eticheta afișată (`labs.suggestions.<cheie>`) se traduce.
 */
const OBSERVATION_SUGGESTIONS: { key: string; note: string }[] = [
  { key: 'ironAnemia', note: 'Anemie feriprivă confirmată' },
  { key: 'vitaminD', note: 'Deficiență de vitamina D' },
  { key: 'vitaminB12', note: 'Deficiență de vitamina B12' },
  { key: 'magnesium', note: 'Deficiență de magneziu' },
  { key: 'zinc', note: 'Deficiență de zinc' },
  { key: 'folate', note: 'Deficiență de folat (vitamina B9)' },
  { key: 'calcium', note: 'Deficiență de calciu' },
  { key: 'iodine', note: 'Deficiență de iod' },
  { key: 'potassium', note: 'Deficiență de potasiu' },
  { key: 'lactose', note: 'Intoleranță la lactoză' },
  { key: 'gluten', note: 'Intoleranță la gluten / boală celiacă' },
  { key: 'hypertension', note: 'Hipertensiune arterială' },
  { key: 'diabetes', note: 'Diabet zaharat / prediabet' },
  { key: 'reflux', note: 'Reflux gastroesofagian' },
  { key: 'kidney', note: 'Boală renală cronică' },
  { key: 'noFish', note: 'Nu pot consuma pește' },
  { key: 'noDairy', note: 'Nu pot consuma lactate' },
  { key: 'noSeeds', note: 'Nu pot consuma semințe' },
]

const emptyInputs = (): LabInputs => ({
  ...(Object.fromEntries(LAB_KEYS.map((k) => [k, ''])) as Record<LabKey, string>),
  notes: '',
})

/** Convertește valoarea din API la string pentru input. Null/undefined/0 → '' (câmp gol, placeholder cu interval estimativ). */
function toInputValue(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return String(v)
}

type PdfMessage = { kind: 'success' | 'warning'; text: string }

const MedicalLabResultsPage = ({ user, onComplete, onBackToDashboard }: MedicalLabResultsPageProps) => {
  const { t } = useTranslation()
  const [inputs, setInputs] = useState<LabInputs>(emptyInputs)

  const [loading, setLoading] = useState(false)
  const [loadingNote, setLoadingNote] = useState<string | null>(null)
  const [loadingExisting, setLoadingExisting] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [extractPdfLoading, setExtractPdfLoading] = useState(false)
  const [extractPdfMessage, setExtractPdfMessage] = useState<PdfMessage | null>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    if (!user?.id) {
      setLoadingExisting(false)
      return
    }
    labResultsService
      .getByUserId(user.id)
      .then((items: LabResult[]) => {
        if (Array.isArray(items) && items.length > 0) {
          const latest = items[0]
          setInputs({
            ...(Object.fromEntries(LAB_KEYS.map((k) => [k, toInputValue(latest[k])])) as Record<LabKey, string>),
            notes: latest.notes ?? '',
          })
        }
      })
      .catch(() => { /* ignoră - utilizatorul poate completa manual */ })
      .finally(() => setLoadingExisting(false))
  }, [user?.id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return
    setLoading(true)
    setError(null)

    try {
      const payload: LabResultsCreatePayload = {
        user_id: user.id || 0,
        notes: inputs.notes?.trim() || '',
      }
      for (const k of LAB_KEYS) {
        const v = parseOptionalDecimal(inputs[k])
        payload[k] = v !== undefined ? v : null
      }

      await labResultsService.create(payload)
      if (user.id) {
        setLoadingNote(t('labs.regenerating'))
        await regenerateRecommendationsAfterSave(user.id)
      }
      setLoadingNote(null)
      onComplete()
    } catch (err: unknown) {
      console.error('Eroare la salvarea analizelor:', err)
      setLoadingNote(null)
      setError(err instanceof Error && err.message ? err.message : t('labs.errors.saveFailed'))
      // Utilizatorul poate continua oricum prin „Sari peste”.
    } finally {
      setLoading(false)
    }
  }

  const handleClearAll = () => {
    setInputs(emptyInputs())
    setError(null)
  }

  const addSuggestion = (note: string) =>
    setInputs((prev) => {
      const current = (prev.notes || '').trim()
      if (!current) return { ...prev, notes: note }
      if (normalizeLabNoteText(current).includes(normalizeLabNoteText(note))) return prev
      return { ...prev, notes: `${current}; ${note}` }
    })

  const handlePdfUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (file) void processPdf(file)
  }

  const handlePdfDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file && !extractPdfLoading) void processPdf(file)
  }

  const processPdf = async (file: File) => {
    if (file.type !== 'application/pdf') {
      setExtractPdfMessage({ kind: 'warning', text: t('labs.pdf.notPdf') })
      return
    }
    setExtractPdfLoading(true)
    setExtractPdfMessage(null)
    setError(null)
    try {
      const text = await extractTextFromPdfFile(file)
      if (!text.trim()) {
        setExtractPdfMessage({ kind: 'warning', text: t('labs.pdf.noText') })
        return
      }
      const localExtracted = extractLabValuesFromTextLocal(text)
      const extracted = await labResultsService.extractFromText(text)
      const extractWarnings = Array.isArray((extracted as { warnings?: unknown }).warnings)
        ? ((extracted as { warnings?: { message?: string; low_confidence?: boolean }[] }).warnings ?? [])
        : []

      const merged: Partial<Record<LabKey, number>> = {}
      for (const k of LAB_KEYS) {
        merged[k] = coerceLabNumeric(extracted[k]) ?? localExtracted[k]
      }
      const foundKeys = LAB_KEYS.filter((k) => merged[k] != null)

      setInputs((prev) => {
        const next = { ...prev }
        for (const k of foundKeys) next[k] = String(merged[k])
        return next
      })

      if (foundKeys.length === 0) {
        setExtractPdfMessage({ kind: 'warning', text: t('labs.pdf.nothingFound') })
        return
      }
      const lowConfidence = extractWarnings.filter((w) => w.low_confidence).length
      const names = foundKeys.map((k) => t(`labs.names.${k}`)).join(', ')
      setExtractPdfMessage({
        kind: 'success',
        text:
          t('labs.pdf.extracted', { count: foundKeys.length, names }) +
          (lowConfidence > 0 ? ` ${t('labs.pdf.lowConfidence', { count: lowConfidence })}` : ''),
      })
    } catch (err) {
      console.error('Eroare la extragerea din PDF:', err)
      setExtractPdfMessage({ kind: 'warning', text: t('labs.pdf.failed') })
    } finally {
      setExtractPdfLoading(false)
    }
  }

  const placeholderFor = (key: LabKey): string | undefined => {
    if (key === 'vitamin_c') return `23–85 μmol/L (${t('labs.approximate')})`
    if (key === 'vitamin_k') return t('labs.vitaminKPlaceholder')
    return LAB_FIELDS[key].range
  }

  const isFilled = (k: LabKey) => parseOptionalDecimal(inputs[k]) !== undefined
  const filled = LAB_KEYS.filter(isFilled).length

  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* Antet: titlu, cât e completat și importul din PDF */}
      <motion.section
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="relative overflow-hidden rounded-card border border-line bg-surface shadow-card"
      >
        <HeroBackdrop />
        <div className="relative p-5 sm:p-6 md:p-8">
          {onBackToDashboard && (
            <button
              type="button"
              onClick={onBackToDashboard}
              className="-ml-1 mb-3 inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg px-1 text-sm font-medium text-zinc-400 transition-colors hover:text-accent touch-manipulation"
            >
              <ArrowLeft aria-hidden="true" className="h-4 w-4" />
              {t('profile.edit.backToRecs')}
            </button>
          )}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3.5">
              <motion.div
                initial={{ scale: 0.6, rotate: -12, opacity: 0 }}
                animate={{ scale: 1, rotate: 0, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 260, damping: 18 }}
                className="relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl border border-accent-border bg-accent-soft text-accent"
              >
                <span aria-hidden="true" className="absolute inset-0 animate-ping-slow rounded-xl border border-accent/40" />
                <FlaskConical aria-hidden="true" className="h-6 w-6" />
              </motion.div>
              <div className="min-w-0">
                <h1 className="bg-gradient-to-r from-zinc-50 via-zinc-100 to-accent-hover bg-clip-text text-2xl font-semibold tracking-tight text-transparent sm:text-3xl">
                  {t('labs.title')}
                </h1>
                <p className="mt-0.5 text-sm text-zinc-400">{t('labs.subtitle')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CompletionRing count={filled} total={LAB_KEYS.length} label={t('labs.completedOf', { count: filled, total: LAB_KEYS.length })} />
              <span aria-hidden="true" className="text-xs text-zinc-500">{t('labs.completed')}</span>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-5">
            <label
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handlePdfDrop}
              className={`group relative flex min-h-[120px] flex-col items-center justify-center gap-2 overflow-hidden rounded-xl border-2 border-dashed px-4 py-5 text-center transition-colors focus-within:border-accent md:col-span-3 ${
                dragging ? 'border-accent bg-accent/10' : 'border-accent-border bg-accent/[0.03] hover:bg-accent-soft'
              } ${extractPdfLoading ? 'cursor-wait' : 'cursor-pointer'}`}
            >
              <input type="file" accept="application/pdf" onChange={handlePdfUpload} disabled={extractPdfLoading} className="sr-only" />
              <span
                className={`flex h-11 w-11 items-center justify-center rounded-full border border-accent-border bg-accent-soft text-accent transition-transform duration-300 ${
                  dragging ? 'scale-110' : 'group-hover:-translate-y-1'
                }`}
              >
                {extractPdfLoading ? <Spinner /> : <FileUp aria-hidden="true" className="h-5 w-5" />}
              </span>
              <span className="text-sm font-semibold text-accent">
                {extractPdfLoading ? t('labs.pdf.processing') : dragging ? t('labs.pdf.dropActive') : t('labs.pdf.choose')}
              </span>
              {!extractPdfLoading && !dragging && <span className="hidden text-xs text-zinc-500 md:block">{t('labs.pdf.drop')}</span>}
              {/* Pe telefon explicația stă în zona de încărcare, nu într-o casetă separată. */}
              <span className="max-w-xs text-xs leading-relaxed text-zinc-500 md:hidden">{t('labs.pdf.description')}</span>
            </label>
            <div className="hidden gap-3 rounded-xl border border-line bg-white/[0.02] p-4 text-sm leading-relaxed text-zinc-400 md:col-span-2 md:flex">
              <Info aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
              <p>
                <strong className="font-semibold text-zinc-200">{t('labs.pdf.title')}</strong> – {t('labs.pdf.description')}
              </p>
            </div>
          </div>
          {extractPdfMessage && (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              role="status"
              className={`mt-3 text-xs leading-relaxed ${extractPdfMessage.kind === 'success' ? 'text-accent' : 'text-amber-300'}`}
            >
              {extractPdfMessage.text}
            </motion.p>
          )}
        </div>
      </motion.section>

      <GlassCard className="w-full !max-w-none">
        <Alert variant="info" className="mb-6">
          <strong className="font-semibold text-zinc-100">{t('labs.noteTitle')}</strong> {t('labs.noteBody')}
        </Alert>

        {loadingExisting && (
          <Alert variant="info" className="mb-5">
            <span className="flex items-center gap-2">
              <Spinner />
              {t('labs.loadingExisting')}
            </span>
          </Alert>
        )}

        {error && <Alert variant="warning" className="mb-5">{error}</Alert>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="space-y-6">
            {LAB_GROUPS.map(({ key, Icon, fields }, gi) => (
              <motion.fieldset
                key={key}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, delay: 0.1 + gi * 0.08, ease: [0.16, 1, 0.3, 1] }}
                className="min-w-0 rounded-xl border border-line bg-white/[0.015] p-3.5 sm:p-5"
              >
                <legend className="sr-only">{t(`labs.groups.${key}`)}</legend>
                <div aria-hidden="true" className="mb-4 flex items-center justify-between gap-3">
                  <p className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
                    <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-accent-border bg-accent-soft text-accent">
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                    {t(`labs.groups.${key}`)}
                  </p>
                  <span className="rounded-full border border-line-strong px-2 py-0.5 text-[11px] tabular-nums text-zinc-400">
                    {fields.filter(isFilled).length}/{fields.length}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-x-3 sm:gap-x-4 lg:grid-cols-3">
                  {fields.map((k) => (
                    <LabField
                      key={k}
                      label={t(`labs.names.${k}`)}
                      unit={LAB_FIELDS[k].unit}
                      value={inputs[k]}
                      onChange={(v) => setInputs((prev) => ({ ...prev, [k]: sanitizeDecimalInput(v) }))}
                      placeholder={placeholderFor(k)}
                      low={LAB_FIELDS[k].low}
                      high={LAB_FIELDS[k].high}
                    />
                  ))}
                </div>
              </motion.fieldset>
            ))}
          </div>

          <div className="mt-6">
            <InputField
              label={t('labs.notes.label')}
              value={inputs.notes || ''}
              onChange={(e) => setInputs((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder={t('labs.notes.placeholder')}
              textarea
              rows={3}
            />
          </div>

          <div className="mb-6 rounded-lg border border-line bg-white/[0.02] p-3.5">
            <p className="mb-2.5 text-xs text-zinc-400">{t('labs.notes.suggestionsTitle')}</p>
            <ul className="flex flex-wrap gap-2">
              {OBSERVATION_SUGGESTIONS.map(({ key, note }) => {
                const added = normalizeLabNoteText(inputs.notes || '').includes(normalizeLabNoteText(note))
                return (
                  <li key={key}>
                    <motion.button
                      type="button"
                      whileTap={{ scale: 0.94 }}
                      onClick={() => addSuggestion(note)}
                      aria-pressed={added}
                      className={`inline-flex min-h-[32px] cursor-pointer items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                        added
                          ? 'border-accent-border bg-accent-soft text-accent'
                          : 'border-line-strong bg-white/[0.03] text-zinc-300 hover:border-accent-border hover:bg-accent-soft hover:text-accent'
                      }`}
                    >
                      {added ? <Check aria-hidden="true" className="h-3 w-3" /> : <Plus aria-hidden="true" className="h-3 w-3" />}
                      {t(`labs.suggestions.${key}`)}
                    </motion.button>
                  </li>
                )
              })}
            </ul>
          </div>

          {/* Pe telefon acțiunea principală e prima; pe ecran lat stă în dreapta. */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="order-3 sm:order-1">
              <PrimaryButton variant="danger" onClick={handleClearAll}>
                <Trash2 aria-hidden="true" className="h-4 w-4" />
                {t('labs.clearAll')}
              </PrimaryButton>
            </div>
            <div className="order-2">
              <PrimaryButton variant="secondary" onClick={onComplete}>
                <SkipForward aria-hidden="true" className="h-4 w-4" />
                {t('labs.skip')}
              </PrimaryButton>
            </div>
            <div className="order-1 sm:order-3">
              <PrimaryButton type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <Spinner />
                    <span>{loadingNote || t('labs.saving')}</span>
                  </>
                ) : (
                  <>
                    <span>{t('profile.create.submit')}</span>
                    <ArrowRight aria-hidden="true" className="h-4 w-4" />
                  </>
                )}
              </PrimaryButton>
            </div>
          </div>
        </form>
      </GlassCard>
    </div>
  )
}

export default MedicalLabResultsPage
