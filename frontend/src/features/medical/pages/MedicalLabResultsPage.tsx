import { useState } from 'react'
import { motion } from 'framer-motion'
import { FlaskConical, ArrowRight, SkipForward } from 'lucide-react'
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components'
import { labResultsService } from '../../../services/api'
import type { User } from '../../../shared/types'

interface MedicalLabResultsPageProps {
  user: User
  onComplete: () => void
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
  notes?: string
}

const MedicalLabResultsPage = ({ user, onComplete }: MedicalLabResultsPageProps) => {
  const [formData, setFormData] = useState<LabResult>({
    user_id: user.id || 0,
    hemoglobin: undefined,
    ferritin: undefined,
    vitamin_d: undefined,
    vitamin_b12: undefined,
    calcium: undefined,
    magnesium: undefined,
    zinc: undefined,
    protein: undefined,
    folate: undefined,
    vitamin_a: undefined,
    iodine: undefined,
    vitamin_k: undefined,
    potassium: undefined,
    notes: ''
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const hasAnyValue = Object.entries(formData).some(
        ([key, value]) => key !== 'user_id' && key !== 'notes' && value !== undefined && value !== null && value !== ''
      )

      if (hasAnyValue) {
        await labResultsService.create(formData)
      }
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

  return (
    <div className="w-full max-w-4xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <GlassCard className="max-w-3xl mx-auto">
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
              Sistemul va folosi estimări bazate pe profilul tău.
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-yellow-500/20 border border-yellow-500/50 text-yellow-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputField
                label="Hemoglobină (g/dL)"
                type="number"
                value={formData.hemoglobin?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, hemoglobin: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="12-16 g/dL"
              />

              <InputField
                label="Feritină (ng/mL)"
                type="number"
                value={formData.ferritin?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, ferritin: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="15-150 ng/mL"
              />

              <InputField
                label="Vitamina D (ng/mL)"
                type="number"
                value={formData.vitamin_d?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, vitamin_d: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="30-100 ng/mL"
              />

              <InputField
                label="Vitamina B12 (pg/mL)"
                type="number"
                value={formData.vitamin_b12?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, vitamin_b12: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="200-900 pg/mL"
              />

              <InputField
                label="Calciu (mg/dL)"
                type="number"
                value={formData.calcium?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, calcium: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="8.5-10.5 mg/dL"
              />

              <InputField
                label="Magneziu (mg/dL)"
                type="number"
                value={formData.magnesium?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, magnesium: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="1.7-2.2 mg/dL"
              />

              <InputField
                label="Zinc (mcg/dL)"
                type="number"
                value={formData.zinc?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, zinc: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="70-100 mcg/dL"
              />

              <InputField
                label="Proteine (g/dL)"
                type="number"
                value={formData.protein?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, protein: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="6.0-8.0 g/dL"
              />

              <InputField
                label="Folat / Acid folic (ng/mL)"
                type="number"
                value={formData.folate?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, folate: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="> 3 ng/mL"
              />

              <InputField
                label="Vitamina A (μg/dL)"
                type="number"
                value={formData.vitamin_a?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, vitamin_a: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="> 20 μg/dL"
              />

              <InputField
                label="Iod (μg/L)"
                type="number"
                value={formData.iodine?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, iodine: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="> 100 μg/L"
              />

              <InputField
                label="Potasiu (mmol/L)"
                type="number"
                value={formData.potassium?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, potassium: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="> 3.5 mmol/L"
              />
            </div>

            <InputField
              label="Observații sau diagnostic medical"
              value={formData.notes || ''}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Adaugă orice observații sau informații suplimentare..."
              textarea={true}
              rows={4}
            />

            <div className="flex gap-4">
              <motion.button
                type="button"
                onClick={handleSkip}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="flex-1 rounded-xl border border-white/10 bg-slate-800/40 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-slate-700/40 transition flex items-center justify-center gap-2"
              >
                <SkipForward className="w-5 h-5" />
                Sari peste
              </motion.button>
              <PrimaryButton type="submit" disabled={loading} full={false} className="flex-1">
                {loading ? 'Se salvează...' : 'Continuă'}
                {!loading && <ArrowRight className="w-5 h-5 ml-2" />}
              </PrimaryButton>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default MedicalLabResultsPage

