import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FlaskConical, ArrowRight, SkipForward, FileUp, Loader2, ArrowLeft, Trash2 } from 'lucide-react'
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components'
import { labResultsService } from '../../../services/api'
import { extractTextFromPdfFile } from '../../../shared/utils/pdfTextExtractor'
import { parseOptionalDecimal, sanitizeDecimalInput } from '../../../shared/utils/numberParsing'
import type { User } from '../../../shared/types'

interface MedicalLabResultsPageProps {
  user: User
  onComplete: () => void
  onBackToDashboard?: () => void
}

interface LabResult {
  user_id: number
  hemoglobin?: number
  ferritin?: number
  vitamin_d?: number
  vitamin_b12?: number
  calcium?: number
  magnesium?: number
  zinc?: number
  protein?: number
  folate?: number
  vitamin_a?: number
  iodine?: number
  vitamin_k?: number
  potassium?: number
  notes?: string
}

type LabKey =
  | 'hemoglobin'
  | 'ferritin'
  | 'vitamin_d'
  | 'vitamin_b12'
  | 'calcium'
  | 'magnesium'
  | 'zinc'
  | 'protein'
  | 'folate'
  | 'vitamin_a'
  | 'iodine'
  | 'vitamin_k'
  | 'potassium'

const LAB_KEYS: LabKey[] = [
  'hemoglobin',
  'ferritin',
  'vitamin_d',
  'vitamin_b12',
  'calcium',
  'magnesium',
  'zinc',
  'protein',
  'folate',
  'vitamin_a',
  'iodine',
  'vitamin_k',
  'potassium',
]

const OBSERVATION_SUGGESTIONS = [
  'Anemie feriprivă confirmată',
  'Deficiență de vitamina D',
  'Deficiență de vitamina B12',
  'Deficiență de magneziu',
  'Deficiență de zinc',
  'Intoleranță la lactoză',
  'Intoleranță la gluten / boală celiacă',
  'Hipertensiune arterială',
  'Diabet zaharat / prediabet',
  'Boală renală cronică',
]

function extractLabValuesFromTextLocal(text: string): Partial<Record<LabKey, number>> {
  const t = (text || '')
    .replace(/\u00a0/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  const tryParse = (raw: string | undefined): number | undefined => {
    if (!raw) return undefined
    const n = Number(raw.replace(',', '.'))
    return Number.isFinite(n) ? n : undefined
  }

  const pickFirst = (patterns: RegExp[]): number | undefined => {
    for (const p of patterns) {
      const m = t.match(p)
      if (m?.[1]) {
        const v = tryParse(m[1])
        if (v !== undefined) return v
      }
    }
    return undefined
  }

  return {
    hemoglobin: pickFirst([
      /\b(?:hemoglobina|hemoglobină|hemoglobin)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\b(?:hgb)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
      /\b(?:hb)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i,
    ]),
    ferritin: pickFirst([/\b(?:feritina|feritină|ferritin)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    vitamin_d: pickFirst([/\b(?:25\s*-?\s*oh\s*-?\s*d|vit(?:\.)?\s*d|vitamina\s*d)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    vitamin_b12: pickFirst([/\b(?:vit(?:\.)?\s*b\s*12|b\s*12|cobalamina)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    calcium: pickFirst([/\b(?:calciu|calcium)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    magnesium: pickFirst([/\b(?:magneziu|magnesium)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    zinc: pickFirst([/\b(?:zinc|zn)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    protein: pickFirst([/\b(?:proteine|protein(?:a)?)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    folate: pickFirst([/\b(?:folat|acid\s*folic|vit(?:\.)?\s*b9)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    vitamin_a: pickFirst([/\b(?:vit(?:\.)?\s*a|vitamina\s*a|retinol)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    iodine: pickFirst([/\b(?:iod|iodine)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    vitamin_k: pickFirst([/\b(?:vit(?:\.)?\s*k|vitamina\s*k)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
    potassium: pickFirst([/\b(?:potasiu|potassium)\b\s*[:-]?\s*(\d+(?:[.,]\d+)?)/i]),
  }
}

/** Convertește valoarea din API la string pentru input. Null/undefined/0 → '' (câmp gol, placeholder cu interval estimativ). */
function toInputValue(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  if (!Number.isFinite(n) || n === 0) return ''
  return String(v)
}

const MedicalLabResultsPage = ({ user, onComplete, onBackToDashboard }: MedicalLabResultsPageProps) => {
  const [inputs, setInputs] = useState<Record<LabKey, string> & { notes: string }>(() => ({
    hemoglobin: '',
    ferritin: '',
    vitamin_d: '',
    vitamin_b12: '',
    calcium: '',
    magnesium: '',
    zinc: '',
    protein: '',
    folate: '',
    vitamin_a: '',
    iodine: '',
    vitamin_k: '',
    potassium: '',
    notes: '',
  }))

  const [loading, setLoading] = useState(false)
  const [loadingExisting, setLoadingExisting] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [extractPdfLoading, setExtractPdfLoading] = useState(false)
  const [extractPdfMessage, setExtractPdfMessage] = useState<string | null>(null)

  useEffect(() => {
    if (user?.id) {
      labResultsService.getByUserId(user.id)
        .then((items: LabResult[]) => {
          if (Array.isArray(items) && items.length > 0) {
            const latest = items[0]
            setInputs({
              hemoglobin: toInputValue(latest.hemoglobin),
              ferritin: toInputValue(latest.ferritin),
              vitamin_d: toInputValue(latest.vitamin_d),
              vitamin_b12: toInputValue(latest.vitamin_b12),
              calcium: toInputValue(latest.calcium),
              magnesium: toInputValue(latest.magnesium),
              zinc: toInputValue(latest.zinc),
              protein: toInputValue(latest.protein),
              folate: toInputValue(latest.folate),
              vitamin_a: toInputValue(latest.vitamin_a),
              iodine: toInputValue(latest.iodine),
              vitamin_k: toInputValue(latest.vitamin_k),
              potassium: toInputValue(latest.potassium),
              notes: latest.notes ?? '',
            })
          }
        })
        .catch(() => { /* ignoră - utilizatorul poate completa manual */ })
        .finally(() => setLoadingExisting(false))
    } else {
      setLoadingExisting(false)
    }
  }, [user?.id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const payload: LabResult & Record<string, unknown> = {
        user_id: user.id || 0,
        notes: inputs.notes?.trim() || '',
      }
      for (const k of LAB_KEYS) {
        const v = parseOptionalDecimal(inputs[k])
        ;(payload as any)[k] = v !== undefined ? v : null
      }

      await labResultsService.create(payload)
      onComplete()
    } catch (err: any) {
      console.error('Eroare la salvarea analizelor:', err)
      let errorMessage = 'Eroare la salvarea analizelor. Poți continua oricum.'
      
      if (err?.message) {
        errorMessage = err.message
      } else if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail)
        }
      }
      
      setError(errorMessage)
      // Continuă chiar dacă e eroare - poate sări peste acest pas
      // Utilizatorul poate continua manual
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = () => {
    onComplete()
  }

  const handleClearAll = () => {
    setInputs({
      hemoglobin: '',
      ferritin: '',
      vitamin_d: '',
      vitamin_b12: '',
      calcium: '',
      magnesium: '',
      zinc: '',
      protein: '',
      folate: '',
      vitamin_a: '',
      iodine: '',
      vitamin_k: '',
      potassium: '',
      notes: '',
    })
    setError(null)
  }

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      setExtractPdfMessage('Te rugăm să încarci un fișier PDF.')
      return
    }
    setExtractPdfLoading(true)
    setExtractPdfMessage(null)
    setError(null)
    e.target.value = ''
    try {
      const text = await extractTextFromPdfFile(file)
      if (!text.trim()) {
        setExtractPdfMessage('Nu s-a putut extrage text din PDF. Poate fișierul este scanat sau protejat.')
        return
      }
      const localExtracted = extractLabValuesFromTextLocal(text)
      const extracted = await labResultsService.extractFromText(text)
      const merged: Partial<Record<LabKey, number>> = {}
      for (const k of LAB_KEYS) {
        const backendVal = (extracted as any)?.[k]
        const localVal = (localExtracted as any)?.[k]
        merged[k] =
          backendVal !== null && backendVal !== undefined && backendVal !== ''
            ? backendVal
            : localVal !== null && localVal !== undefined && localVal !== ''
              ? localVal
              : undefined
      }
      const knownKeyLabels: Record<string, string> = {
        hemoglobin: 'Hemoglobină',
        ferritin: 'Feritină',
        vitamin_d: 'Vitamina D',
        vitamin_b12: 'Vitamina B12',
        calcium: 'Calciu',
        magnesium: 'Magneziu',
        zinc: 'Zinc',
        protein: 'Proteine',
        folate: 'Folat / Acid folic',
        vitamin_a: 'Vitamina A',
        iodine: 'Iod',
        vitamin_k: 'Vitamina K',
        potassium: 'Potasiu',
      }
      const extractedKnownKeys = Object.keys(knownKeyLabels).filter((k) => {
        const v = (merged as any)?.[k]
        return v != null && v !== undefined && v !== ''
      })
      const count = extractedKnownKeys.length
      setInputs(prev => ({
        ...prev,
        hemoglobin: merged.hemoglobin != null ? String(merged.hemoglobin) : prev.hemoglobin,
        ferritin: merged.ferritin != null ? String(merged.ferritin) : prev.ferritin,
        vitamin_d: merged.vitamin_d != null ? String(merged.vitamin_d) : prev.vitamin_d,
        vitamin_b12: merged.vitamin_b12 != null ? String(merged.vitamin_b12) : prev.vitamin_b12,
        calcium: merged.calcium != null ? String(merged.calcium) : prev.calcium,
        magnesium: merged.magnesium != null ? String(merged.magnesium) : prev.magnesium,
        zinc: merged.zinc != null ? String(merged.zinc) : prev.zinc,
        protein: merged.protein != null ? String(merged.protein) : prev.protein,
        folate: merged.folate != null ? String(merged.folate) : prev.folate,
        vitamin_a: merged.vitamin_a != null ? String(merged.vitamin_a) : prev.vitamin_a,
        iodine: merged.iodine != null ? String(merged.iodine) : prev.iodine,
        vitamin_k: merged.vitamin_k != null ? String(merged.vitamin_k) : prev.vitamin_k,
        potassium: merged.potassium != null ? String(merged.potassium) : prev.potassium,
      }))
      setExtractPdfMessage(count > 0
        ? `S-au extras ${count} valori: ${extractedKnownKeys.map((k) => knownKeyLabels[k] || k).join(', ')}. Verifică și completează manual dacă e cazul.`
        : 'Nu s-au identificat valori cunoscute în raport. Introdu manual.')
    } catch (err) {
      console.error('Eroare la extragerea din PDF:', err)
      setExtractPdfMessage('Eroare la procesarea PDF-ului. Încearcă din nou sau introdu manual.')
    } finally {
      setExtractPdfLoading(false)
    }
  }

  return (
    <div className="w-full max-w-4xl lg:max-w-[90vw]">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <GlassCard className="w-full max-w-3xl lg:max-w-none mx-auto lg:min-h-[80vh]">
          {onBackToDashboard && (
            <button
              type="button"
              onClick={onBackToDashboard}
              className="mb-4 min-h-[44px] inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-neonCyan transition touch-manipulation"
            >
              <ArrowLeft className="w-5 h-5" />
              Înapoi la recomandări
            </button>
          )}
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-tr from-neonPurple to-neonMagenta p-3 rounded-lg shadow-neon">
              <FlaskConical className="w-6 h-6 text-black" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100">Rezultate analize medicale</h2>
              <p className="text-slate-400 text-sm">Introdu valorile din analizele recente (opțional)</p>
            </div>
          </div>

          <div className="bg-blue-900/30 border border-blue-500/30 rounded-xl p-4 mb-6">
            <p className="text-sm text-blue-200">
              <strong>Notă:</strong> Dacă nu ai analize recente, poți sări peste acest pas. 
              Poți șterge orice valoare (sau toate) și salva – recomandările se vor actualiza 
              pe baza noilor date și a profilului tău.
            </p>
          </div>

          <div className="mb-6 p-4 rounded-xl border border-neonCyan/30 bg-neonCyan/5">
            <p className="text-sm text-slate-300 mb-3">
              <strong>Încarcă raport medical PDF</strong> – atașează raportul tău medical în format PDF și sistemul va extrage automat valorile pentru câmpurile disponibile.
            </p>
            <label className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-dashed border-neonCyan/50 text-neonCyan hover:bg-neonCyan/10 cursor-pointer transition font-medium text-sm">
              <input
                type="file"
                accept="application/pdf"
                onChange={handlePdfUpload}
                disabled={extractPdfLoading}
                className="hidden"
              />
              {extractPdfLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Se procesează PDF-ul...
                </>
              ) : (
                <>
                  <FileUp className="w-5 h-5" />
                  Alege raport PDF
                </>
              )}
            </label>
            {extractPdfMessage && (
              <p className={`mt-3 text-xs ${extractPdfMessage.includes('S-au extras') ? 'text-green-400' : 'text-amber-400'}`}>
                {extractPdfMessage}
              </p>
            )}
          </div>

          {loadingExisting && (
            <div className="mb-4 p-3 rounded-lg bg-slate-700/50 border border-slate-500/30 text-slate-300 text-sm flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Se încarcă analizele existente...
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-yellow-500/20 border border-yellow-500/50 text-yellow-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputField
                label="Hemoglobină (g/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.hemoglobin}
                onChange={(e) => setInputs({ ...inputs, hemoglobin: sanitizeDecimalInput(e.target.value) })}
                placeholder="12-16 g/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Feritină (ng/mL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.ferritin}
                onChange={(e) => setInputs({ ...inputs, ferritin: sanitizeDecimalInput(e.target.value) })}
                placeholder="15-150 ng/mL"
                transparentWhenEmpty
              />

              <InputField
                label="Vitamina D (ng/mL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.vitamin_d}
                onChange={(e) => setInputs({ ...inputs, vitamin_d: sanitizeDecimalInput(e.target.value) })}
                placeholder="30-100 ng/mL"
                transparentWhenEmpty
              />

              <InputField
                label="Vitamina B12 (pg/mL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.vitamin_b12}
                onChange={(e) => setInputs({ ...inputs, vitamin_b12: sanitizeDecimalInput(e.target.value) })}
                placeholder="200-900 pg/mL"
                transparentWhenEmpty
              />

              <InputField
                label="Calciu (mg/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.calcium}
                onChange={(e) => setInputs({ ...inputs, calcium: sanitizeDecimalInput(e.target.value) })}
                placeholder="8.5-10.5 mg/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Magneziu (mg/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.magnesium}
                onChange={(e) => setInputs({ ...inputs, magnesium: sanitizeDecimalInput(e.target.value) })}
                placeholder="1.7-2.2 mg/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Zinc (mcg/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.zinc}
                onChange={(e) => setInputs({ ...inputs, zinc: sanitizeDecimalInput(e.target.value) })}
                placeholder="70-100 mcg/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Proteine (g/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.protein}
                onChange={(e) => setInputs({ ...inputs, protein: sanitizeDecimalInput(e.target.value) })}
                placeholder="6.0-8.0 g/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Folat / Acid folic (ng/mL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.folate}
                onChange={(e) => setInputs({ ...inputs, folate: sanitizeDecimalInput(e.target.value) })}
                placeholder="> 3 ng/mL"
                transparentWhenEmpty
              />

              <InputField
                label="Vitamina A (μg/dL)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.vitamin_a}
                onChange={(e) => setInputs({ ...inputs, vitamin_a: sanitizeDecimalInput(e.target.value) })}
                placeholder="> 20 μg/dL"
                transparentWhenEmpty
              />

              <InputField
                label="Iod (μg/L)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.iodine}
                onChange={(e) => setInputs({ ...inputs, iodine: sanitizeDecimalInput(e.target.value) })}
                placeholder="> 100 μg/L"
                transparentWhenEmpty
              />

              <InputField
                label="Potasiu (mmol/L)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={inputs.potassium}
                onChange={(e) => setInputs({ ...inputs, potassium: sanitizeDecimalInput(e.target.value) })}
                placeholder="> 3.5 mmol/L"
                transparentWhenEmpty
              />
            </div>

            <InputField
              label="Observații sau diagnostic medical"
              value={inputs.notes || ''}
              onChange={(e) => setInputs({ ...inputs, notes: e.target.value })}
              placeholder="Adaugă orice observații sau informații suplimentare..."
              textarea={true}
              rows={4}
            />
            <div className="rounded-lg border border-slate-600/40 bg-slate-800/30 p-3">
              <p className="mb-2 text-xs text-slate-300">
                Sugestii utile pentru observații (apasă pentru a adăuga):
              </p>
              <div className="flex flex-wrap gap-2">
                {OBSERVATION_SUGGESTIONS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() =>
                      setInputs((prev) => {
                        const current = (prev.notes || '').trim()
                        if (!current) return { ...prev, notes: item }
                        if (current.toLowerCase().includes(item.toLowerCase())) return prev
                        return { ...prev, notes: `${current}; ${item}` }
                      })
                    }
                    className="rounded-full border border-neonCyan/40 bg-neonCyan/10 px-3 py-1.5 text-xs font-medium text-neonCyan hover:bg-neonCyan/20 transition"
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 items-stretch flex-wrap">
              <button
                type="button"
                onClick={handleClearAll}
                className="w-full sm:flex-1 min-h-[44px] rounded-xl border border-rose-500/40 bg-rose-500/10 px-6 py-3.5 text-sm font-semibold text-rose-300 hover:bg-rose-500/20 transition inline-flex items-center justify-center gap-2 touch-manipulation"
              >
                <Trash2 className="w-5 h-5" />
                Șterge toate valorile
              </button>
              <button
                type="button"
                onClick={handleSkip}
                className="w-full sm:flex-1 min-h-[44px] rounded-xl border border-white/10 bg-slate-800/40 px-6 py-3.5 text-sm font-semibold text-slate-200 hover:bg-slate-700/40 transition inline-flex items-center justify-center gap-2 touch-manipulation"
              >
                <SkipForward className="w-5 h-5" />
                Sari peste
              </button>
              <div className="w-full sm:flex-1">
                <PrimaryButton type="submit" disabled={loading} full={true}>
                  {loading ? 'Se salvează...' : 'Continuă'}
                  {!loading && <ArrowRight className="w-5 h-5 ml-2" />}
                </PrimaryButton>
              </div>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default MedicalLabResultsPage

