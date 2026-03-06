import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { UserCog, Save, FlaskConical } from 'lucide-react'
import React from 'react'
import { GlassCard, InputField, SelectField, PrimaryButton, AllergySelector, MedicalConditionSelector } from '../../../shared/components'
import { profileService } from '../../../services/api'
import type { User } from '../../../shared/types'

interface EditProfilePageProps {
  user: User
  onUpdate: (user: User) => void
  onNavigateBack: () => void
  onNavigateToLabResults?: () => void
}

const EditProfilePage = ({ user, onUpdate, onNavigateBack, onNavigateToLabResults }: EditProfilePageProps) => {
  const [formData, setFormData] = useState<Partial<User>>({
    email: user.email,
    name: user.name,
    age: user.age,
    sex: user.sex,
    weight: user.weight,
    height: user.height,
    activity_level: user.activity_level,
    diet_type: user.diet_type,
    allergies: user.allergies || '',
    medical_conditions: user.medical_conditions || ''
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    // Load user data from backend when component mounts if user has ID
    if (user.id) {
      loadUserData()
    }
    // Otherwise, formData is already initialized with user prop data
  }, [user.id])

  const loadUserData = async () => {
    try {
      if (user.id) {
        const response = await profileService.get(user.id)
        setFormData({
          email: response.email,
          name: response.name,
          age: response.age,
          sex: response.sex,
          weight: response.weight,
          height: response.height,
          activity_level: response.activity_level,
          diet_type: response.diet_type,
          allergies: response.allergies || '',
          medical_conditions: response.medical_conditions || ''
        })
      }
    } catch (error) {
      console.error('Eroare la încărcarea datelor:', error)
      // If loading fails, keep the initial user data that was passed as prop
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      // Backend uses email to identify and update user
      const response = await profileService.update(user.id || 0, formData)
      setSuccess(true)
      
      // Actualizează utilizatorul cu datele noi
      const updatedUser = {
        ...user,
        ...response
      }
      onUpdate(updatedUser)
      
      // Navigate back after a short delay
      setTimeout(() => {
        onNavigateBack()
      }, 1500)
    } catch (err: any) {
      console.error('Eroare la actualizarea profilului:', err)
      // Extrage mesajul de eroare
      let errorMessage = 'Eroare la salvarea modificărilor. Te rugăm să încerci din nou.'
      
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
    } finally {
      setLoading(false)
    }
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
            <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-3 rounded-lg shadow-neon">
              <UserCog className="w-6 h-6 text-black" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100">Actualizează profilul</h2>
              <p className="text-slate-400 text-sm">Modifică informațiile tale personale</p>
            </div>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-300 text-sm"
            >
              {error}
            </motion.div>
          )}

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 p-3 rounded-lg bg-green-500/20 border border-green-500/50 text-green-300 text-sm"
            >
              Profilul a fost actualizat cu succes!
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <InputField
                label="Nume complet"
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Nume Prenume"
              />

              <InputField
                label="Email"
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="exemplu@email.com"
              />

              <div>
                <InputField
                  label="Vârstă"
                  type="number"
                  value={formData.age?.toString() || ''}
                  onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 25 })}
                  placeholder="25"
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
                type="number"
                step="0.1"
                value={formData.weight?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) || 70 })}
                placeholder="70"
              />

              <InputField
                label="Înălțime (cm)"
                type="number"
                step="0.1"
                value={formData.height?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, height: parseFloat(e.target.value) || 170 })}
                placeholder="170"
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

            {onNavigateToLabResults && (
              <div className="mb-6 p-4 rounded-xl border border-neonPurple/30 bg-neonPurple/10">
                <p className="text-sm text-slate-300 mb-3">
                  Actualizează și rezultatele analizelor medicale pentru recomandări mai precise pe baza valorilor tale (hemoglobină, feritină, vitamine etc.).
                </p>
                <button
                  type="button"
                  onClick={onNavigateToLabResults}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-neonPurple/50 text-neonPurple hover:bg-neonPurple/20 transition font-medium text-sm"
                >
                  <FlaskConical className="w-5 h-5" />
                  Actualizează analize medicale
                </button>
              </div>
            )}

            <div className="mt-6 flex gap-4">
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
                    <Save className="w-5 h-5" />
                    <span>Salvează modificările</span>
                  </>
                )}
              </PrimaryButton>
              <button
                type="button"
                onClick={onNavigateBack}
                className="px-6 py-3 rounded-xl border border-white/20 text-slate-300 hover:border-neonCyan hover:text-neonCyan transition font-medium"
              >
                Anulează
              </button>
            </div>
          </form>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default EditProfilePage

