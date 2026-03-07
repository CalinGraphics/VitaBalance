import { User, Activity, Scale, Ruler, Heart, AlertTriangle } from 'lucide-react'
import { GlassCard } from '../../../shared/components'
import type { User as UserType } from '../../../shared/types'
import { formatAllergiesString, formatMedicalConditionsString } from '../../../shared/utils/formatters'

interface UserProfileInfoProps {
  user: UserType
}

const UserProfileInfo = ({ user }: UserProfileInfoProps) => {
  const getActivityLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      sedentary: 'Sedentary',
      moderate: 'Moderat',
      active: 'Activ',
      very_active: 'Foarte activ'
    }
    return labels[level] || level
  }

  const getDietTypeLabel = (diet: string) => {
    const labels: Record<string, string> = {
      omnivore: 'Omnivor',
      vegetarian: 'Vegetarian',
      vegan: 'Vegan',
      pescatarian: 'Pescetarian'
    }
    return labels[diet] || diet
  }

  const getSexLabel = (sex: string) => {
    const labels: Record<string, string> = {
      M: 'Masculin',
      F: 'Feminin',
      other: 'Altul'
    }
    return labels[sex] || sex
  }

  return (
    <GlassCard className="w-full max-w-none !max-w-full">
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-2 rounded-lg flex-shrink-0">
          <User className="w-5 h-5 text-black" />
        </div>
        <h3 className="text-lg sm:text-xl font-bold text-slate-100">Profil Utilizator</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Date biometrice */}
        <div className="flex items-start gap-2">
          <Scale className="w-5 h-5 text-neonCyan flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Greutate</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.weight ? `${user.weight} kg` : 'N/A'}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <Ruler className="w-5 h-5 text-neonCyan flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Înălțime</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.height ? `${user.height} cm` : 'N/A'}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <User className="w-5 h-5 text-neonCyan flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Vârstă</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.age ? `${user.age} ani` : 'N/A'}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <Heart className="w-5 h-5 text-neonCyan flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Sex</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.sex ? getSexLabel(user.sex) : 'N/A'}
            </p>
          </div>
        </div>

        {/* Activitate și dietă */}
        <div className="flex items-start gap-2">
          <Activity className="w-5 h-5 text-neonPurple flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Nivel activitate</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.activity_level ? getActivityLevelLabel(user.activity_level) : 'N/A'}
            </p>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <User className="w-5 h-5 text-neonPurple flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs text-slate-400">Tip dietă</p>
            <p className="text-sm font-semibold text-slate-100">
              {user.diet_type ? getDietTypeLabel(user.diet_type) : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Alergii și condiții medicale */}
      {(user.allergies || user.medical_conditions) && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          {user.allergies && (
            <div className="flex items-start gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-slate-400 mb-1">Alergii</p>
                <p className="text-sm text-slate-200">{formatAllergiesString(user.allergies)}</p>
              </div>
            </div>
          )}

          {user.medical_conditions && (
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-slate-400 mb-1">Condiții medicale</p>
                <p className="text-sm text-slate-200">{formatMedicalConditionsString(user.medical_conditions)}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </GlassCard>
  )
}

export default UserProfileInfo

