// Valorile canonice ale condițiilor medicale (stocate în baza de date).
// Etichetele și descrierile sunt traduse în shared/i18n/locales/*.json (cheile `conditions.<valoare>.*`).
export const MEDICAL_CONDITION_VALUES = [
  'diabet',
  'hipertensiune',
  'anemie',
  'osteoporoza',
  'tiroida',
  'celiachie',
  'boli_cardiovasculare',
  'insuficienta_renala',
  'reflux',
  'iritații_intestinale',
  'deficienta_vitamin_d',
  'deficienta_b12',
  'obezitate',
  'colesterol_ridicat',
  'gout',
] as const

export const parseMedicalConditions = (str: string | undefined | null): string[] => {
  if (!str) return []
  return str
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)
}

export const stringifyMedicalConditions = (conditions: string[]): string => {
  return conditions.filter(c => c.length > 0).join(', ')
}
