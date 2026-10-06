/** Model recomandare afișat în UI (API + feedback local). */
export interface Recommendation {
  food_id: number
  food: {
    id: number
    name: string
    category: string
    /** Categoria stabilă din catalogul validat (nuts, legumes, ...). */
    category_key?: string | null
    /** kcal la 100 g (din catalogul de alimente); lipsește în răspunsuri mai vechi. */
    calories?: number
  }
  score: number
  /** % din necesarul zilnic al nutrientului principal acoperit de porție (aceeași cifră în grafic și pe card). */
  coverage: number
  explanation: {
    text: string
    portion: number
    /** Unitate afișare: "g" (implicit) sau "ml" pentru băuturi. */
    portion_unit?: 'g' | 'ml' | string
    reasons: string[]
    tips?: string[]
    alternatives?: string[]
  }
  recommendation_id: number
  feedback?: {
    likes: number
    dislikes: number
  }
  my_rating?: number | null
}
