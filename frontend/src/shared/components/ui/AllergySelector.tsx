import { useTranslation } from 'react-i18next'
import { ALLERGY_VALUES, parseAllergies, stringifyAllergies } from '../../constants/allergies'
import { formatAllergy } from '../../utils/formatters'
import MultiSelectField from './MultiSelectField'

interface AllergySelectorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const AllergySelector = ({ label, value, onChange, placeholder }: AllergySelectorProps) => {
  const { t } = useTranslation()
  const options = ALLERGY_VALUES.map((v) => ({
    value: v,
    label: t(`allergies.${v}.label`),
    description: t(`allergies.${v}.description`),
  }))

  return (
    <MultiSelectField
      label={label}
      selected={parseAllergies(value)}
      options={options}
      onChange={(next) => onChange(stringifyAllergies(next))}
      placeholder={placeholder ?? t('selectors.allergiesPlaceholder')}
      summary={(count) => t('selectors.allergiesSelected', { count })}
      hint={t('selectors.allergiesHint')}
      fallbackLabel={formatAllergy}
    />
  )
}

export default AllergySelector
