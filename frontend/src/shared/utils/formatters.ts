// Mapping pentru categorii de alimente
const CATEGORY_MAPPINGS: Record<string, string> = {
  'carne': 'Carne',
  'peste': 'Pește',
  'legume': 'Legume',
  'lactate': 'Lactate',
  'cereale': 'Cereale',
  'fructe_seci': 'Fructe seci',
  'fructe seci': 'Fructe seci',
  'semințe': 'Semințe',
  'semnite': 'Semințe', // fallback pentru fără diacritice
  'seminte': 'Semințe',
  'fructe': 'Fructe',
  'leguminoase': 'Leguminoase',
  'ouă': 'Ouă',
  'oua': 'Ouă',
  'unt': 'Unt',
  'ulei': 'Ulei',
  'ciuperci': 'Ciuperci',
  'nuci': 'Nuci',
  'soia': 'Soia',
  'alune': 'Alune'
}

/** Categorii compuse din CSV (Cereale/Procesate) — prioritate, ca cerealele să nu apară ca lactate. */
const COMPOUND_CATEGORY_PRIORITY: Array<{ match: string; label: string }> = [
  { match: 'bauturi', label: 'Băuturi' },
  { match: 'deserturi', label: 'Deserturi' },
  { match: 'cereale', label: 'Cereale' },
  { match: 'leguminoase', label: 'Leguminoase' },
  { match: 'legume', label: 'Legume' },
  { match: 'fructe', label: 'Fructe' },
  { match: 'peste', label: 'Pește' },
  { match: 'carne', label: 'Carne' },
  { match: 'oua', label: 'Ouă' },
  { match: 'ouă', label: 'Ouă' },
  { match: 'nuci', label: 'Nuci' },
  { match: 'semin', label: 'Semințe' },
  { match: 'lactate', label: 'Lactate' },
  { match: 'lapte', label: 'Lactate' },
  { match: 'suplimente', label: 'Suplimente' },
  { match: 'condimente', label: 'Condimente' },
  { match: 'gustari', label: 'Gustări' },
  { match: 'mese', label: 'Mese' },
  { match: 'proteine', label: 'Proteine' },
  { match: 'paste', label: 'Paste' },
]

function normalizeCategoryPath(category: string): string {
  return category
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

// Formatare categorie alimentară
export const formatFoodCategory = (category: string | undefined | null): string => {
  if (!category) return ''

  const norm = normalizeCategoryPath(category)

  if (CATEGORY_MAPPINGS[norm]) {
    return CATEGORY_MAPPINGS[norm]
  }

  if (norm.includes('/')) {
    const parts = norm.split('/').map((p) => p.trim())
    for (const { match, label } of COMPOUND_CATEGORY_PRIORITY) {
      if (parts.some((p) => p.includes(match))) {
        return label
      }
    }
  }

  for (const { match, label } of COMPOUND_CATEGORY_PRIORITY) {
    if (norm.includes(match)) {
      return label
    }
  }

  let formatted = category.replace(/_/g, ' ')
  formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1).toLowerCase()
  return formatted
}

/** Cheie pentru grupare filtre (cereale vs cereale/procesate). */
export const foodCategoryGroupKey = (category: string | undefined | null): string => {
  if (!category) return 'alte'
  const norm = normalizeCategoryPath(category)
  for (const { match } of COMPOUND_CATEGORY_PRIORITY) {
    if (norm.includes(match)) return match
  }
  return norm.split('/')[0] || 'alte'
}

// Formatare alergie - folosește label-urile din COMMON_ALLERGIES
import { COMMON_ALLERGIES } from '../constants/allergies'
import { parseAllergies } from '../constants/allergies'
import { COMMON_MEDICAL_CONDITIONS, parseMedicalConditions } from '../constants/medicalConditions'

export const formatAllergy = (allergyValue: string): string => {
  const allergy = COMMON_ALLERGIES.find(a => a.value === allergyValue.toLowerCase().trim())
  return allergy ? allergy.label : allergyValue.charAt(0).toUpperCase() + allergyValue.slice(1).toLowerCase()
}

// Formatare string de alergii (comma-separated)
export const formatAllergiesString = (allergiesString: string | undefined | null): string => {
  if (!allergiesString) return ''
  
  const allergies = parseAllergies(allergiesString)
  return allergies.map(formatAllergy).join(', ')
}

export const formatMedicalCondition = (conditionValue: string): string => {
  const key = conditionValue.toLowerCase().trim()
  const item = COMMON_MEDICAL_CONDITIONS.find(c => c.value === key)
  if (item) return item.label
  // fallback: înlocuiește underscore-uri și capitalizează
  const cleaned = conditionValue.replace(/_/g, ' ').trim()
  return cleaned.length > 0 ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1).toLowerCase() : ''
}

export const formatMedicalConditionsString = (conditionsString: string | undefined | null): string => {
  if (!conditionsString) return ''
  const conditions = parseMedicalConditions(conditionsString)
  return conditions.map(formatMedicalCondition).join(', ')
}
