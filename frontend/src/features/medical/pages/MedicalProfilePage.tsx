import { useState } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, ArrowRight } from 'lucide-react'
import React from 'react'
import { GlassCard, InputField, SelectField, PrimaryButton } from '../../../shared/components'
import { profileService } from '../../../services/api'
import type { User, AuthUser } from '../../../shared/types'

interface MedicalProfilePageProps {
  authUser: AuthUser
  onComplete: (user: User) => void
}

const MedicalProfilePage = ({ authUser, onComplete }: MedicalProfilePageProps) => {
  const [formData, setFormData] = useState<Partial<User>>({
    email: authUser.email,
    name: authUser.fullName,
    age: 25,
    sex: 'F',
    weight: 70,
    height: 170,
    activity_level: 'moderate',
    diet_type: 'omnivore',
    allergies: '',
    medical_conditions: ''
  })

  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await profileService.create(formData)
      onComplete(response)
    } catch (error) {
      console.error('Eroare la salvarea profilului:', error)
      // Mock pentru demo - continuă cu datele locale
      onComplete(formData as User)
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
              <UserPlus className="w-6 h-6 text-black" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100">Profilul tău medical</h2>
              <p className="text-slate-400 text-sm">Completează informațiile pentru recomandări personalizate</p>
            </div>
          </div>

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
                value={formData.weight?.toString() || ''}
                onChange={(e) => setFormData({ ...formData, weight: parseFloat(e.target.value) || 70 })}
                placeholder="70"
              />

              <InputField
                label="Înălțime (cm)"
                type="number"
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

            <InputField
              label="Alergii"
              value={formData.allergies || ''}
              onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
              placeholder="EX: lactoza, nuci, gluten"
            />

            <InputField
              label="Condiții medicale"
              value={formData.medical_conditions || ''}
              onChange={(e) => setFormData({ ...formData, medical_conditions: e.target.value })}
              placeholder="EX: diabet, hipertensiune"
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

