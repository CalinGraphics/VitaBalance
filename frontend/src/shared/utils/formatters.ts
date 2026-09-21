import i18n from '../i18n'
import { parseAllergies } from '../constants/allergies'
import { parseMedicalConditions } from '../constants/medicalConditions'

// Mapping categorie normalizată (fără diacritice, lowercase) -> cheie i18n `categories.<cheie>`
const CATEGORY_KEYS: Record<string, string> = {
  'carne': 'carne',
  'peste': 'peste',
  'legume': 'legume',
  'lactate': 'lactate',
  'cereale': 'cereale',
  'fructe_seci': 'fructe_seci',
  'fructe seci': 'fructe_seci',
  'seminte': 'seminte',
  'semnite': 'seminte', // fallback pentru fără diacritice
  'fructe': 'fructe',
  'leguminoase': 'leguminoase',
  'oua': 'oua',
  'unt': 'unt',
  'ulei': 'ulei',
  'ciuperci': 'ciuperci',
  'nuci': 'nuci',
  'soia': 'soia',
  'alune': 'alune',
}

/** Categorii compuse din CSV (Cereale/Procesate) — prioritate, ca cerealele să nu apară ca lactate. */
const COMPOUND_CATEGORY_PRIORITY: Array<{ match: string; key: string }> = [
  { match: 'bauturi', key: 'bauturi' },
  { match: 'deserturi', key: 'deserturi' },
  { match: 'cereale', key: 'cereale' },
  { match: 'leguminoase', key: 'leguminoase' },
  { match: 'legume', key: 'legume' },
  { match: 'fructe', key: 'fructe' },
  { match: 'peste', key: 'peste' },
  { match: 'carne', key: 'carne' },
  { match: 'oua', key: 'oua' },
  { match: 'nuci', key: 'nuci' },
  { match: 'semin', key: 'seminte' },
  { match: 'lactate', key: 'lactate' },
  { match: 'lapte', key: 'lactate' },
  { match: 'suplimente', key: 'suplimente' },
  { match: 'condimente', key: 'condimente' },
  { match: 'gustari', key: 'gustari' },
  { match: 'mese', key: 'mese' },
  { match: 'proteine', key: 'proteine' },
  { match: 'paste', key: 'paste' },
]

function normalizeCategoryPath(category: string): string {
  return category
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

const categoryLabel = (key: string): string => i18n.t(`categories.${key}`)

/**
 * Rezolvă categoria unui aliment: `key` e stabilă (independentă de limbă — potrivită pentru filtre),
 * `label` e tradusă în limba curentă. `null` când lipsește categoria.
 */
export const resolveFoodCategory = (
  category: string | undefined | null
): { key: string; label: string } | null => {
  if (!category) return null

  const norm = normalizeCategoryPath(category)
  const known = (key: string) => ({ key, label: categoryLabel(key) })

  if (CATEGORY_KEYS[norm]) return known(CATEGORY_KEYS[norm])

  if (norm.includes('/')) {
    const parts = norm.split('/').map((p) => p.trim())
    for (const { match, key } of COMPOUND_CATEGORY_PRIORITY) {
      if (parts.some((p) => p.includes(match))) return known(key)
    }
  }

  for (const { match, key } of COMPOUND_CATEGORY_PRIORITY) {
    if (norm.includes(match)) return known(key)
  }

  const cleaned = category.replace(/_/g, ' ')
  return { key: `raw:${norm}`, label: cleaned.charAt(0).toUpperCase() + cleaned.slice(1).toLowerCase() }
}

// Formatare categorie alimentară (tradusă în limba curentă)
export const formatFoodCategory = (category: string | undefined | null): string =>
  resolveFoodCategory(category)?.label ?? ''

const capitalize = (raw: string): string => {
  const cleaned = raw.replace(/_/g, ' ').trim()
  return cleaned.length > 0 ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1).toLowerCase() : ''
}

// Formatare alergie - eticheta tradusă din `allergies.<valoare>.label`
export const formatAllergy = (allergyValue: string): string => {
  const key = allergyValue.toLowerCase().trim()
  return i18n.t(`allergies.${key}.label`, { defaultValue: capitalize(allergyValue) })
}

// Formatare string de alergii (comma-separated)
export const formatAllergiesString = (allergiesString: string | undefined | null): string => {
  if (!allergiesString) return ''
  return parseAllergies(allergiesString).map(formatAllergy).join(', ')
}

export const formatMedicalCondition = (conditionValue: string): string => {
  const key = conditionValue.toLowerCase().trim()
  return i18n.t(`conditions.${key}.label`, { defaultValue: capitalize(conditionValue) })
}

export const formatMedicalConditionsString = (conditionsString: string | undefined | null): string => {
  if (!conditionsString) return ''
  return parseMedicalConditions(conditionsString).map(formatMedicalCondition).join(', ')
}
