import { useTranslation } from 'react-i18next'
import { InputField, SelectField, AllergySelector, MedicalConditionSelector } from '../../../shared/components'
import { sanitizeDecimalInput, sanitizeIntInput } from '../../../shared/utils/numberParsing'
import { CALORIC_GOAL_MAX, CALORIC_GOAL_MIN, type ProfileForm } from '../hooks/useProfileForm'

const SEX_VALUES = ['F', 'M', 'other'] as const
const ACTIVITY_VALUES = ['sedentary', 'moderate', 'active', 'very_active'] as const
const DIET_VALUES = ['omnivore', 'vegetarian', 'vegan', 'pescatarian'] as const

/** Câmpurile formularului de profil (folosit la creare și la editare). */
const ProfileFormFields = ({ form }: { form: ProfileForm }) => {
  const { t } = useTranslation()
  const { formData, update } = form

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-x-4 md:grid-cols-2">
        <InputField
          label={t('profile.fields.name')}
          value={formData.name}
          onChange={(e) => update({ name: e.target.value })}
          placeholder={t('profile.fields.namePlaceholder')}
          autoComplete="name"
        />
        <InputField
          label={t('profile.fields.email')}
          type="email"
          value={formData.email}
          onChange={(e) => update({ email: e.target.value })}
          placeholder={t('profile.fields.emailPlaceholder')}
          autoComplete="email"
        />
        <InputField
          label={t('profile.fields.age')}
          inputMode="numeric"
          pattern="[0-9]*"
          value={form.ageText}
          onChange={(e) => form.setAgeText(sanitizeIntInput(e.target.value))}
          placeholder="25"
        />
        <SelectField
          label={t('profile.fields.sex')}
          value={formData.sex}
          onChange={(e) => update({ sex: e.target.value })}
          options={SEX_VALUES.map((v) => ({ value: v, label: t(`profile.options.sex.${v}`) }))}
        />
        <InputField
          label={t('profile.fields.weight')}
          inputMode="decimal"
          pattern="[0-9]*[.,]?[0-9]*"
          value={form.weightText}
          onChange={(e) => form.setWeightText(sanitizeDecimalInput(e.target.value))}
          placeholder="70"
        />
        <InputField
          label={t('profile.fields.height')}
          inputMode="decimal"
          pattern="[0-9]*[.,]?[0-9]*"
          value={form.heightText}
          onChange={(e) => form.setHeightText(sanitizeDecimalInput(e.target.value))}
          placeholder="170"
        />
        <SelectField
          label={t('profile.fields.activity')}
          value={formData.activity_level}
          onChange={(e) => update({ activity_level: e.target.value })}
          options={ACTIVITY_VALUES.map((v) => ({ value: v, label: t(`profile.options.activity.${v}`) }))}
        />
        <SelectField
          label={t('profile.fields.diet')}
          value={formData.diet_type}
          onChange={(e) => update({ diet_type: e.target.value })}
          options={DIET_VALUES.map((v) => ({ value: v, label: t(`profile.options.diet.${v}`) }))}
        />
        <InputField
          label={`${t('profile.fields.caloricGoal')} (${t('common.optional')})`}
          inputMode="numeric"
          pattern="[0-9]*"
          value={form.caloricGoalText}
          onChange={(e) => form.setCaloricGoalText(sanitizeIntInput(e.target.value))}
          placeholder="2000"
          hint={t('profile.fields.caloricGoalHint', { min: CALORIC_GOAL_MIN, max: CALORIC_GOAL_MAX })}
          transparentWhenEmpty
        />
      </div>

      <AllergySelector
        label={t('profile.fields.allergies')}
        value={formData.allergies}
        onChange={(value) => update({ allergies: value })}
      />

      <MedicalConditionSelector
        label={t('profile.fields.conditions')}
        value={formData.medical_conditions}
        onChange={(value) => update({ medical_conditions: value })}
      />
    </div>
  )
}

export default ProfileFormFields
