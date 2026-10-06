/**
 * Recomandare primită de la API — independentă de limbă: fapte (chei, cifre, id-uri de reguli) și numele în ambele
 * limbi. Textul afișat se construiește în browser (explanations/buildExplanation.ts), deci schimbarea limbii nu
 * face nicio cerere la server.
 */
export interface Need {
  nutrient?: string
  source: 'lab' | 'notes' | 'general'
  severity?: 'mild' | 'moderate' | 'severe'
  daily_reference?: number
  marker?: string
  value?: number
  threshold?: number
  unit?: string
}

export interface FactNutrient {
  key: string
  /** Cantitatea din porție, în unitatea catalogului. */
  amount: number
  per100: number
  daily_reference: number
  /** % din necesarul zilnic acoperit de porție (plafonat la 100). */
  pct: number
  need: Need
}

export interface Facts {
  v: number
  food_id: number
  food_key?: string | null
  category?: string | null
  animal?: string | null
  portion: { amount: number; unit: 'g' | 'ml' | string; label_ro?: string | null; label_en?: string | null }
  kcal_portion?: number | null
  has_lab_data: boolean
  nutrients: FactNutrient[]
  primary?: string | null
  coverage_pct?: number
  profile: { diet: string | null; allergies: string[]; conditions: string[] }
  safety_rules: string[]
  flags: string[]
  alternatives: number[]
  trace?: unknown
}

export interface Recommendation {
  food_id: number
  recommendation_id: number
  food: {
    id: number
    name_ro: string
    name_en: string
    /** Eticheta RO a categoriei (catalog vechi); pentru catalogul validat se folosește `category_key`. */
    category: string
    category_key?: string | null
    /** kcal la 100 g (doar catalogul validat). */
    calories?: number | null
  }
  score: number
  /** % din necesarul zilnic al nutrientului principal acoperit de porție (aceeași cifră în grafic și pe card). */
  coverage: number
  facts: Facts | null
  alternatives: { id: number; name_ro: string; name_en: string }[]
  /** Text salvat (RO) pentru rândurile vechi, fără fapte. */
  legacy: { text: string; reasons: string[]; tips: string[] } | null
  feedback?: {
    likes: number
    dislikes: number
  }
  my_rating?: number | null
}
