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

// Formatare categorie alimentară
export const formatFoodCategory = (category: string | undefined | null): string => {
  if (!category) return ''
  
  const categoryLower = category.toLowerCase().trim()
  
  // Verifică dacă există mapping direct
  if (CATEGORY_MAPPINGS[categoryLower]) {
    return CATEGORY_MAPPINGS[categoryLower]
  }
  
  // Dacă nu există mapping, formatează manual
  // Înlocuiește underscore-uri cu spații
  let formatted = category.replace(/_/g, ' ')
  
  // Capitalize prima literă
  formatted = formatted.charAt(0).toUpperCase() + formatted.slice(1).toLowerCase()
  
  return formatted
}

// Formatare alergie - folosește label-urile din COMMON_ALLERGIES
import { COMMON_ALLERGIES } from '../constants/allergies'
import { parseAllergies } from '../constants/allergies'

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
