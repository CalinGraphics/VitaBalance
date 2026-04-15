import axios from 'axios'
import type { User } from '../shared/types'
import { getToken, clearToken } from './authStorage'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Helper function pentru extragerea mesajului de eroare
const extractErrorMessage = (error: any): string => {
  // Dacă există un detail în răspuns
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    
    // Dacă detail este un string, returnează-l direct
    if (typeof detail === 'string') {
      return detail
    }
    
    // Dacă detail este un array (erori de validare Pydantic)
    if (Array.isArray(detail)) {
      return detail
        .map((err: any) => {
          // Extrage mesajul din fiecare eroare
          if (typeof err === 'string') {
            return err
          }
          if (err.msg) {
            const loc = err.loc ? err.loc.join('.') : ''
            return loc ? `${loc}: ${err.msg}` : err.msg
          }
          return JSON.stringify(err)
        })
        .join('; ')
    }
    
    // Dacă detail este un obiect, convertește-l în string
    if (typeof detail === 'object') {
      return detail.msg || detail.message || JSON.stringify(detail)
    }
  }
  
  // Încearcă alte câmpuri comune
  if (error.response?.data?.message) {
    return typeof error.response.data.message === 'string' 
      ? error.response.data.message 
      : JSON.stringify(error.response.data.message)
  }
  
  if (error.message) {
    return error.message
  }
  
  return 'A apărut o eroare neașteptată'
}

// Interceptor pentru gestionarea erorilor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url: string = error.config?.url || ''

    // Nu șterge tokenul dacă 401 vine de la verificarea magic link-ului.
    // În dev, React StrictMode poate apela de două ori verificarea, iar al doilea apel va eșua cu 401.
    if (
      status === 401 &&
      !url.includes('/auth/verify-magic-link') &&
      !url.includes('/auth/request-magic-link')
    ) {
      clearToken()
    }
    // Pentru toate status-urile (inclusiv 404) formatează un mesaj clar,
    // dar păstrează codul de status în error.response.status.
    error.message = extractErrorMessage(error)
    return Promise.reject(error)
  }
)

// Auth (magic link + JWT)
export const authService = {
  requestMagicLink: async (email: string, fullName?: string) => {
    const response = await api.post('/auth/request-magic-link', {
      email: email.trim(),
      ...(fullName ? { fullName: fullName.trim() } : {}),
    })
    return response.data
  },
  verifyMagicLink: async (token: string) => {
    const response = await api.post('/auth/verify-magic-link', { token })
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// API Services
export const profileService = {
  create: async (data: Partial<User>) => {
    const response = await api.post('/profile', data)
    return response.data
  },
  getByEmail: async (email: string) => {
    const response = await api.get(`/profile/by-email/${email}`)
    return response.data
  },
  get: async (userId: number) => {
    const response = await api.get(`/profile/${userId}`)
    return response.data
  },
  update: async (userId: number, data: Partial<User>) => {
    const response = await api.post('/profile', { ...data, id: userId })
    return response.data
  },
}

export const labResultsService = {
  create: async (data: any) => {
    const response = await api.post('/lab-results', data)
    return response.data
  },
  getByUserId: async (userId: number) => {
    const response = await api.get(`/lab-results/${userId}`)
    return response.data
  },
  extractFromText: async (text: string) => {
    const response = await api.post('/lab-results/extract-from-text', { text })
    return response.data
  },
}

export const recommendationsService = {
  get: async (
    userId: number,
    forceRegenerate: boolean = false,
    opts?: { replaceRecommendationId?: number }
  ) => {
    const body: Record<string, unknown> = { user_id: userId }
    if (opts?.replaceRecommendationId) {
      body.replace_recommendation_id = opts.replaceRecommendationId
    }
    const response = await api.post(
      `/recommendations?force_regenerate=${forceRegenerate}`,
      body
    )
    return response.data
  },
  replace: async (userId: number, recommendationId: number) => {
    const response = await api.post('/recommendations', {
      user_id: userId,
      replace_recommendation_id: recommendationId,
    })
    return response.data
  },
  regenerate: async (userId: number) => {
    try {
      await api.delete(`/recommendations/${userId}`)
    } catch (err) {
      console.log('Nu există recomandări de șters:', err)
    }
    const response = await api.post('/recommendations', { user_id: userId })
    return response.data
  },
}

export const feedbackService = {
  create: async (data: { user_id: number; recommendation_id: number; rating: number }) => {
    const response = await api.post('/feedback', data)
    return response.data
  },
}

export default api

