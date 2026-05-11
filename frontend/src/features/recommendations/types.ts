/** Model recomandare afișat în UI (API + feedback local). */
export interface Recommendation {
  food_id: number
  food: {
    id: number
    name: string
    category: string
    image_url?: string
  }
  score: number
  coverage: number
  explanation: {
    text: string
    portion: number
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
