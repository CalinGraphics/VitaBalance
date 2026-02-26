// Lista de condiții medicale comune relevante pentru recomandări nutriționale
export interface MedicalConditionOption {
  value: string
  label: string
  description?: string
}

export const COMMON_MEDICAL_CONDITIONS: MedicalConditionOption[] = [
  { value: 'diabet', label: 'Diabet', description: 'Necesită atenție la glucide și indice glicemic' },
  { value: 'hipertensiune', label: 'Hipertensiune', description: 'Limitare sodiu, dietă sănătoasă pentru inimă' },
  { value: 'anemie', label: 'Anemie / deficiență de fier', description: 'Alimente bogate în fier și vitamina C' },
  { value: 'osteoporoza', label: 'Osteoporoza', description: 'Calciu, vitamina D, magneziu' },
  { value: 'tiroida', label: 'Boli de tiroidă', description: 'Iod, seleniu; evitat excesul de soia în unele cazuri' },
  { value: 'celiachie', label: 'Celiachie / intoleranță gluten', description: 'Dietă fără gluten' },
  { value: 'boli_cardiovasculare', label: 'Boli cardiovasculare', description: 'Dietă săracă în sodiu, grasimi sănătoase' },
  { value: 'insuficienta_renala', label: 'Insuficiență renală', description: 'Limitare potasiu, fosfor, proteine (în funcție de stadiu)' },
  { value: 'reflux', label: 'Reflux gastroesofagian', description: 'Evitat mese mari, alimente acide/grase' },
  { value: 'iritații_intestinale', label: 'Sindrom colon iritabil', description: 'Fibre adaptate, evitat trigger-ele personale' },
  { value: 'deficienta_vitamin_d', label: 'Deficiență vitamina D', description: 'Alimente cu vitamina D, expunere la soare' },
  { value: 'deficienta_b12', label: 'Deficiență vitamina B12', description: 'Carne, pește, ouă; suplimente dacă e cazul' },
  { value: 'obezitate', label: 'Obezitate / management greutate', description: 'Echilibru caloric, nutrienți de calitate' },
  { value: 'colesterol_ridicat', label: 'Colesterol ridicat', description: 'Grasimi nesaturate, fibre, evitat trans' },
  { value: 'gout', label: 'Gută', description: 'Limitare purine (carne roșie, fructe de mare), hidratare' },
]

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
