import { useTranslation } from 'react-i18next'
import {
  MEDICAL_CONDITION_VALUES,
  parseMedicalConditions,
  stringifyMedicalConditions,
} from '../../constants/medicalConditions'
import { formatMedicalCondition } from '../../utils/formatters'
import MultiSelectField from './MultiSelectField'

interface MedicalConditionSelectorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const MedicalConditionSelector = ({
  label,
  value,
  onChange,
  placeholder,
}: MedicalConditionSelectorProps) => {
  const { t } = useTranslation()
  const options = MEDICAL_CONDITION_VALUES.map((v) => ({
    value: v,
    label: t(`conditions.${v}.label`),
    description: t(`conditions.${v}.description`),
  }))

  return (
    <MultiSelectField
      label={label}
      selected={parseMedicalConditions(value)}
      options={options}
      onChange={(next) => onChange(stringifyMedicalConditions(next))}
      placeholder={placeholder ?? t('selectors.conditionsPlaceholder')}
      summary={(count) => t('selectors.conditionsSelected', { count })}
      hint={t('selectors.conditionsHint')}
      fallbackLabel={formatMedicalCondition}
    />
  )
}

export default MedicalConditionSelector
