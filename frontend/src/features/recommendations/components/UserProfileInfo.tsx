import { User, Activity, Scale, Ruler, Heart, Utensils, Flame, AlertTriangle, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard } from '../../../shared/components'
import type { User as UserType } from '../../../shared/types'
import { formatAllergiesString, formatMedicalConditionsString } from '../../../shared/utils/formatters'

interface UserProfileInfoProps {
  user: UserType
}

const Stat = ({ Icon, label, value }: { Icon: LucideIcon; label: string; value: string }) => (
  <div className="flex items-start gap-2.5">
    <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-accent" />
    <div className="min-w-0">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="text-sm font-semibold text-zinc-100">{value}</p>
    </div>
  </div>
)

const UserProfileInfo = ({ user }: UserProfileInfoProps) => {
  const { t } = useTranslation()
  const na = t('profile.summary.na')

  /** Traduce o valoare canonică (ex. `very_active`) sau o afișează ca atare dacă e necunoscută. */
  const option = (group: 'sex' | 'activity' | 'diet', value: string | undefined) =>
    value ? t(`profile.options.${group}.${value}`, { defaultValue: value }) : na

  return (
    <GlassCard className="w-full !max-w-full">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border border-accent-border bg-accent-soft text-accent">
          <User aria-hidden="true" className="h-4 w-4" />
        </div>
        <h2 className="text-lg font-semibold tracking-tight text-zinc-50 sm:text-xl">{t('profile.summary.title')}</h2>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-5 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
        <Stat Icon={Scale} label={t('profile.summary.weight')} value={user.weight ? `${user.weight} kg` : na} />
        <Stat Icon={Ruler} label={t('profile.summary.height')} value={user.height ? `${user.height} cm` : na} />
        <Stat
          Icon={User}
          label={t('profile.summary.age')}
          value={user.age ? t('profile.summary.years', { count: user.age }) : na}
        />
        <Stat Icon={Heart} label={t('profile.summary.sex')} value={option('sex', user.sex)} />
        <Stat Icon={Activity} label={t('profile.summary.activity')} value={option('activity', user.activity_level)} />
        <Stat Icon={Utensils} label={t('profile.summary.diet')} value={option('diet', user.diet_type)} />
        {user.caloric_goal != null && user.caloric_goal > 0 && (
          <Stat Icon={Flame} label={t('profile.summary.caloricGoal')} value={`${user.caloric_goal} kcal`} />
        )}
      </div>

      {(user.allergies || user.medical_conditions) && (
        <div className="mt-5 space-y-3 border-t border-line pt-5">
          {user.allergies && (
            <div className="flex items-start gap-2.5">
              <AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
              <div>
                <p className="mb-0.5 text-xs text-zinc-500">{t('profile.fields.allergies')}</p>
                <p className="text-sm text-zinc-200">{formatAllergiesString(user.allergies)}</p>
              </div>
            </div>
          )}

          {user.medical_conditions && (
            <div className="flex items-start gap-2.5">
              <AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
              <div>
                <p className="mb-0.5 text-xs text-zinc-500">{t('profile.fields.conditions')}</p>
                <p className="text-sm text-zinc-200">{formatMedicalConditionsString(user.medical_conditions)}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </GlassCard>
  )
}

export default UserProfileInfo
