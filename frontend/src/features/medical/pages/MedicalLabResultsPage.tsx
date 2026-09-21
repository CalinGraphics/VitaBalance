import React, { useState, useEffect } from 'react'
import { FlaskConical, ArrowRight, SkipForward, FileUp, ArrowLeft, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, InputField, PrimaryButton, PageHeader, Alert, Spinner } from '../../../shared/components'
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

/** Unitatea și intervalul orientativ (placeholder) pentru fiecare analiză; numele vine din i18n (`labs.names.<cheie>`). */
const LAB_FIELDS: { key: LabKey; unit: string; range?: string }[] = [
  { key: 'hemoglobin', unit: 'g/dL', range: '12-16 g/dL' },
  { key: 'ferritin', unit: 'ng/mL', range: '15-150 ng/mL' },
  { key: 'vitamin_d', unit: 'ng/mL', range: '30-100 ng/mL' },
  { key: 'vitamin_b12', unit: 'pg/mL', range: '200-900 pg/mL' },
  { key: 'calcium', unit: 'mg/dL', range: '8.5-10.5 mg/dL' },
  { key: 'magnesium', unit: 'mg/dL', range: '1.7-2.2 mg/dL' },
  { key: 'zinc', unit: 'mcg/dL', range: '70-100 mcg/dL' },
  { key: 'protein', unit: 'g/dL', range: '6.0-8.0 g/dL' },
  { key: 'folate', unit: 'ng/mL', range: '> 3 ng/mL' },
  { key: 'vitamin_a', unit: 'μg/dL', range: '> 20 μg/dL' },
  { key: 'vitamin_c', unit: 'μmol/L' },
  { key: 'iodine', unit: 'μg/L', range: '> 100 μg/L' },
  { key: 'vitamin_k', unit: 'ng/mL' },
  { key: 'potassium', unit: 'mmol/L', range: '> 3.5 mmol/L' },
]

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

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      setExtractPdfMessage({ kind: 'warning', text: t('labs.pdf.notPdf') })
      return
    }
    setExtractPdfLoading(true)
    setExtractPdfMessage(null)
    setError(null)
    e.target.value = ''
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

  const placeholderFor = (key: LabKey, range?: string): string | undefined => {
    if (key === 'vitamin_c') return `23–85 μmol/L (${t('labs.approximate')})`
    if (key === 'vitamin_k') return t('labs.vitaminKPlaceholder')
    return range
  }

  return (
    <div className="w-full max-w-3xl">
      <GlassCard className="mx-auto w-full">
        {onBackToDashboard && (
          <button
            type="button"
            onClick={onBackToDashboard}
            className="-ml-1 mb-4 inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg px-1 text-sm font-medium text-zinc-400 transition-colors hover:text-accent touch-manipulation"
          >
            <ArrowLeft aria-hidden="true" className="h-4 w-4" />
            {t('profile.edit.backToRecs')}
          </button>
        )}

        <PageHeader Icon={FlaskConical} title={t('labs.title')} subtitle={t('labs.subtitle')} />

        <Alert variant="info" className="mb-5">
          <strong className="font-semibold text-zinc-100">{t('labs.noteTitle')}</strong> {t('labs.noteBody')}
        </Alert>

        <div className="mb-6 rounded-lg border border-line bg-white/[0.02] p-4">
          <p className="mb-3 text-sm leading-relaxed text-zinc-400">
            <strong className="font-semibold text-zinc-200">{t('labs.pdf.title')}</strong> – {t('labs.pdf.description')}
          </p>
          <label
            className={`flex min-h-[44px] items-center justify-center gap-2 rounded-lg border border-dashed border-accent-border px-4 py-2.5 text-sm font-medium text-accent transition-colors focus-within:border-accent ${
              extractPdfLoading ? 'cursor-wait opacity-70' : 'cursor-pointer hover:bg-accent-soft'
            }`}
          >
            <input
              type="file"
              accept="application/pdf"
              onChange={handlePdfUpload}
              disabled={extractPdfLoading}
              className="sr-only"
            />
            {extractPdfLoading ? (
              <>
                <Spinner />
                {t('labs.pdf.processing')}
              </>
            ) : (
              <>
                <FileUp aria-hidden="true" className="h-4 w-4" />
                {t('labs.pdf.choose')}
              </>
            )}
          </label>
          {extractPdfMessage && (
            <p
              role="status"
              className={`mt-3 text-xs leading-relaxed ${
                extractPdfMessage.kind === 'success' ? 'text-accent' : 'text-amber-300'
              }`}
            >
              {extractPdfMessage.text}
            </p>
          )}
        </div>

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
          <div className="grid grid-cols-1 gap-x-4 md:grid-cols-2">
            {LAB_FIELDS.map(({ key, unit, range }) => (
              <InputField
                key={key}
                label={`${t(`labs.names.${key}`)} (${unit})`}
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs[key]}
                onChange={(e) => setInputs((prev) => ({ ...prev, [key]: sanitizeDecimalInput(e.target.value) }))}
                placeholder={placeholderFor(key, range)}
                transparentWhenEmpty
              />
            ))}
          </div>

          <InputField
            label={t('labs.notes.label')}
            value={inputs.notes || ''}
            onChange={(e) => setInputs((prev) => ({ ...prev, notes: e.target.value }))}
            placeholder={t('labs.notes.placeholder')}
            textarea
            rows={4}
          />

          <div className="mb-6 rounded-lg border border-line bg-white/[0.02] p-3.5">
            <p className="mb-2.5 text-xs text-zinc-400">{t('labs.notes.suggestionsTitle')}</p>
            <ul className="flex flex-wrap gap-2">
              {OBSERVATION_SUGGESTIONS.map(({ key, note }) => (
                <li key={key}>
                  <button
                    type="button"
                    onClick={() => addSuggestion(note)}
                    className="min-h-[32px] cursor-pointer rounded-full border border-line-strong bg-white/[0.03] px-3 py-1 text-xs font-medium text-zinc-300 transition-colors hover:border-accent-border hover:bg-accent-soft hover:text-accent"
                  >
                    {t(`labs.suggestions.${key}`)}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <PrimaryButton variant="danger" onClick={handleClearAll}>
              <Trash2 aria-hidden="true" className="h-4 w-4" />
              {t('labs.clearAll')}
            </PrimaryButton>
            <PrimaryButton variant="secondary" onClick={onComplete}>
              <SkipForward aria-hidden="true" className="h-4 w-4" />
              {t('labs.skip')}
            </PrimaryButton>
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
        </form>
      </GlassCard>
    </div>
  )
}

export default MedicalLabResultsPage
