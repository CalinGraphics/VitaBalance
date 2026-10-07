export interface CaloricGoalWarning {
  code: 'below_bmr' | 'far_from_tdee'
  goal: number
  bmr: number
  tdee: number
  deviation_pct: number
}

export interface User {
  id?: number
  email: string
  name: string
  age: number
  sex: string
  weight: number
  height: number
  activity_level: string
  diet_type: string
  allergies?: string
  medical_conditions?: string
  /** Obiectiv caloric zilnic (kcal) — opțional, doar informativ; nu influențează recomandările. */
  caloric_goal?: number | null
  /** Avertisment informativ calculat de backend (Mifflin-St Jeor); textul se construiește din locales. */
  caloric_goal_warning?: CaloricGoalWarning | null
  /** Link semnat, temporar, către poza de profil din Supabase Storage (null = fără poză). */
  avatar_url?: string | null
  /** ISO datetime de la API — folosit la polling după regenerare async */
  updated_at?: string | null
}

export interface AuthUser {
  fullName: string
  email: string
  avatarUrl: string | null
}

export type Route = 'login' | 'register' | 'medical-profile' | 'lab-results' | 'recommendations' | 'edit-profile' | 'progress'
