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
  /** ISO datetime de la API — folosit la polling după regenerare async */
  updated_at?: string | null
}

export interface AuthUser {
  fullName: string
  email: string
  bio: string
  avatarUrl: string | null
}

export type Route = 'login' | 'register' | 'auth-verify' | 'medical-profile' | 'lab-results' | 'recommendations' | 'edit-profile'
