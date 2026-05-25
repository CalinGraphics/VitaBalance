/** Model recomandare afișat în UI (API + feedback local). */
export interface Recommendation {
  food_id: number
  food: {
    id: number
    name: string
    category: string
  }
  score: number
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
