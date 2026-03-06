// Lista de alergii comune cu mapping către categorii și cuvinte cheie
export interface AllergyOption {
  value: string
  label: string
  description?: string
}

export const COMMON_ALLERGIES: AllergyOption[] = [
  {
    value: 'lactoza',
    label: 'Lactoză / Lactate',
    description: 'Alergii la produse lactate (lapte, brânză, iaurt, etc.)'
  },
  {
    value: 'gluten',
    label: 'Gluten',
    description: 'Alergii la produse cu gluten (grâu, pâine, paste, etc.)'
  },
  {
    value: 'nuci',
    label: 'Nuci',
    description: 'Alergii la nuci, alune, migdale, fistic, etc.'
  },
  {
    value: 'oua',
    label: 'Ouă',
    description: 'Alergii la ouă și produse care conțin ouă'
  },
  {
    value: 'soia',
    label: 'Soia',
    description: 'Alergii la soia și produse derivate (tofu, tempeh, etc.)'
  },
  {
    value: 'peste',
    label: 'Pește',
    description: 'Alergii la pește și produse din pește'
  },
  {
    value: 'crustacee',
    label: 'Crustacee',
    description: 'Alergii la creveți, crab, homar, etc.'
  },
  {
    value: 'arahide',
    label: 'Arahide',
    description: 'Alergii la arahide și produse care conțin arahide'
  },
  {
    value: 'sesam',
    label: 'Sesam',
    description: 'Alergii la semințe de susan și produse care conțin susan'
  },
  {
    value: 'mustar',
    label: 'Muștar',
    description: 'Alergii la muștar și produse care conțin muștar'
  }
]

// Funcție helper pentru a converti string de alergii în array
export const parseAllergies = (allergiesString: string | undefined | null): string[] => {
  if (!allergiesString) return []
  return allergiesString
    .split(',')
    .map(a => a.trim())
    .filter(a => a.length > 0)
}

// Funcție helper pentru a converti array de alergii în string
export const stringifyAllergies = (allergies: string[]): string => {
  return allergies.filter(a => a.length > 0).join(', ')
}
