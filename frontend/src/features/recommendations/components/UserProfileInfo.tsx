import { motion } from 'framer-motion'
import { User, Activity, Scale, Ruler, Heart, Utensils, Flame, AlertTriangle, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { User as UserType } from '../../../shared/types'
import { formatAllergiesString, formatMedicalConditionsString } from '../../../shared/utils/formatters'

interface UserProfileInfoProps {
  user: UserType
}

const Chip = ({ Icon, label, value, index, warn = false }: { Icon: LucideIcon; label: string; value: string; index: number; warn?: boolean }) => (
  <motion.li
    initial={{ opacity: 0, y: 6 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.35, delay: 0.15 + index * 0.04 }}
    className={`inline-flex min-w-0 max-w-full items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${
      warn ? 'border-amber-400/30 bg-amber-400/[0.07]' : 'border-line-strong bg-white/[0.03]'
    }`}
  >
    <Icon aria-hidden="true" className={`h-3.5 w-3.5 flex-shrink-0 ${warn ? 'text-amber-300' : 'text-accent'}`} />
    <span className="text-zinc-500">{label}</span>
    <span className={`truncate font-semibold ${warn ? 'text-amber-100' : 'text-zinc-100'}`}>{value}</span>
  </motion.li>
)

/** Profilul pe scurt, ca un rând de etichete: ocupă puțin loc, mai ales pe telefon. */
const UserProfileInfo = ({ user }: UserProfileInfoProps) => {
  const { t } = useTranslation()
  const na = t('profile.summary.na')

  /** Traduce o valoare canonică (ex. `very_active`) sau o afișează ca atare dacă e necunoscută. */
  const option = (group: 'sex' | 'activity' | 'diet', value: string | undefined) =>
    value ? t(`profile.options.${group}.${value}`, { defaultValue: value }) : na

  const chips: { Icon: LucideIcon; label: string; value: string; warn?: boolean }[] = [
    { Icon: Scale, label: t('profile.summary.weight'), value: user.weight ? `${user.weight} kg` : na },
    { Icon: Ruler, label: t('profile.summary.height'), value: user.height ? `${user.height} cm` : na },
    { Icon: User, label: t('profile.summary.age'), value: user.age ? t('profile.summary.years', { count: user.age }) : na },
    { Icon: Heart, label: t('profile.summary.sex'), value: option('sex', user.sex) },
    { Icon: Activity, label: t('profile.summary.activity'), value: option('activity', user.activity_level) },
    { Icon: Utensils, label: t('profile.summary.diet'), value: option('diet', user.diet_type) },
  ]
  if (user.caloric_goal != null && user.caloric_goal > 0) {
    chips.push({ Icon: Flame, label: t('profile.summary.caloricGoal'), value: `${user.caloric_goal} kcal` })
  }
  if (user.allergies) {
    chips.push({ Icon: AlertTriangle, label: t('profile.fields.allergies'), value: formatAllergiesString(user.allergies), warn: true })
  }
  if (user.medical_conditions) {
    chips.push({ Icon: AlertTriangle, label: t('profile.fields.conditions'), value: formatMedicalConditionsString(user.medical_conditions), warn: true })
  }

  return (
    <section aria-label={t('profile.summary.title')}>
      <ul className="flex flex-wrap gap-2">
        {chips.map((c, i) => <Chip key={c.label} index={i} {...c} />)}
      </ul>
    </section>
  )
}

export default UserProfileInfo
