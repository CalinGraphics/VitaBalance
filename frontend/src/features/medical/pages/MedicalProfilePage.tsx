import { useState } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, ArrowRight } from 'lucide-react'
import React from 'react'
import { GlassCard, InputField, SelectField, PrimaryButton, AllergySelector, MedicalConditionSelector } from '../../../shared/components'
import { profileService } from '../../../services/api'
import { parseOptionalDecimal, parseOptionalInt, sanitizeDecimalInput, sanitizeIntInput } from '../../../shared/utils/numberParsing'
import type { User, AuthUser } from '../../../shared/types'

interface MedicalProfilePageProps {
  authUser: AuthUser
  onComplete: (user: User) => void
}

const MedicalProfilePage = ({ authUser, onComplete }: MedicalProfilePageProps) => {
  const [formData, setFormData] = useState<Partial<User>>({
    email: authUser.email,
    name: '',
    sex: 'F',
    activity_level: 'moderate',
    diet_type: 'omnivore',
    allergies: '',
    medical_conditions: ''
  })
  const [ageText, setAgeText] = useState('')
  const [weightText, setWeightText] = useState('')
  const [heightText, setHeightText] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const age = parseOptionalInt(ageText)
      const weight = parseOptionalDecimal(weightText)
      const height = parseOptionalDecimal(heightText)

      if (age === undefined) {
        setError('Vârsta este obligatorie.')
        return
      }
      if (weight === undefined) {
        setError('Greutatea este obligatorie.')
        return
      }
      if (height === undefined) {
        setError('Înălțimea este obligatorie.')
        return
      }

      const payload: Partial<User> = {
        ...formData,
        age,
        weight,
        height,
      }

      const response = await profileService.create(payload)
      onComplete(response)
    } catch (err: any) {
      console.error('Eroare la salvarea profilului:', err)
      let errorMessage = 'Eroare la salvarea profilului. Te rugăm să încerci din nou.'
      const detail = err?.response?.data?.detail
      if (detail !== undefined && detail !== null) {
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail)
        }
      } else if (err?.message) {
        errorMessage = err.message
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-full md:max-w-4xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <GlassCard className="w-full max-w-full md:max-w-3xl mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-3 rounded-lg shadow-neon">
              <UserPlus className="w-6 h-6 text-black" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100">Profilul tău medical</h2>
              <p className="text-slate-400 text-sm">Completează informațiile pentru recomandări personalizate</p>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputField
                label="Nume complet"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Introduceți numele complet"
              />

              <InputField
                label="Email"
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="Adresă de email"
              />

              <div>
                <InputField
                  label="Vârstă"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  value={ageText}
                  onChange={(e) => setAgeText(sanitizeIntInput(e.target.value))}
                  placeholder="Introduceți vârsta"
                />
              </div>

              <SelectField
                label="Sex"
                value={formData.sex || ''}
                onChange={(e) => setFormData({ ...formData, sex: e.target.value })}
                options={[
                  { value: 'F', label: 'Feminin' },
                  { value: 'M', label: 'Masculin' },
                  { value: 'other', label: 'Altul' },
                ]}
              />

              <InputField
                label="Greutate (kg)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={weightText}
                onChange={(e) => setWeightText(sanitizeDecimalInput(e.target.value))}
                placeholder="Introduceți greutatea (kg)"
              />

              <InputField
                label="Înălțime (cm)"
                type="text"
                inputMode="decimal"
                pattern="[0-9]*[.,]?[0-9]*"
                value={heightText}
                onChange={(e) => setHeightText(sanitizeDecimalInput(e.target.value))}
                placeholder="Introduceți înălțimea (cm)"
              />

              <SelectField
                label="Nivel de activitate"
                value={formData.activity_level || ''}
                onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
                options={[
                  { value: 'sedentary', label: 'Sedentar' },
                  { value: 'moderate', label: 'Moderat' },
                  { value: 'active', label: 'Activ' },
                  { value: 'very_active', label: 'Foarte activ' },
                ]}
              />

              <SelectField
                label="Tip de dietă"
                value={formData.diet_type || ''}
                onChange={(e) => setFormData({ ...formData, diet_type: e.target.value })}
                options={[
                  { value: 'omnivore', label: 'Omnivor' },
                  { value: 'vegetarian', label: 'Vegetarian' },
                  { value: 'vegan', label: 'Vegan' },
                  { value: 'pescatarian', label: 'Pescetarian' },
                ]}
              />
            </div>

            <AllergySelector
              label="Alergii"
              value={formData.allergies || ''}
              onChange={(value) => setFormData({ ...formData, allergies: value })}
              placeholder="Selectează alergiile tale"
            />

            <MedicalConditionSelector
              label="Condiții medicale"
              value={formData.medical_conditions || ''}
              onChange={(value) => setFormData({ ...formData, medical_conditions: value })}
              placeholder="Selectează condițiile medicale"
            />

            <div className="mt-6">
              <PrimaryButton type="submit" disabled={loading}>
                {loading ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                      className="w-5 h-5 border-2 border-slate-950 border-t-transparent rounded-full"
                    />
                    <span>Se salvează...</span>
                  </>
                ) : (
                  <>
                    <span>Continuă</span>
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </PrimaryButton>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default MedicalProfilePage

