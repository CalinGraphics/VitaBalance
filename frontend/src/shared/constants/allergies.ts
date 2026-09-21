// Valorile canonice ale alergiilor (stocate în baza de date).
// Etichetele și descrierile sunt traduse în shared/i18n/locales/*.json (cheile `allergies.<valoare>.*`).
export const ALLERGY_VALUES = [
  'lactoza',
  'gluten',
  'nuci',
  'oua',
  'soia',
  'peste',
  'crustacee',
  'arahide',
  'sesam',
  'mustar',
] as const

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
