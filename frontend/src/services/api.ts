import axios, { isAxiosError } from 'axios'
import type { User } from '../shared/types'
import { extractErrorMessage } from '../shared/utils/apiErrors'
import { currentLanguage } from '../shared/i18n'
import type { LabExtractFromApi, LabKey } from '../features/medical/utils/labLocalExtract'
import { getToken, clearToken } from './authStorage'

function normalizeApiBaseUrl(raw: string | undefined): string {
  const fallback = '/api'
  if (raw == null || String(raw).trim() === '') return fallback
  const u = String(raw).trim().replace(/\/+$/, '')
  if (!/^https?:\/\//i.test(u)) return u || fallback
  try {
    const parsed = new URL(u)
    const path = (parsed.pathname || '/').replace(/\/+$/, '') || '/'
    if (path === '/' || path === '') {
      parsed.pathname = '/api'
      return parsed.toString().replace(/\/+$/, '')
    }
    return u
  } catch {
    return fallback
  }
}

const API_BASE_URL = normalizeApiBaseUrl(import.meta.env.VITE_API_URL)

const DEFAULT_TIMEOUT_MS = 45_000
const REC_STORED_TIMEOUT_MS = 30_000
const REC_REPLACE_TIMEOUT_MS = 60_000
const REC_MATERIALIZE_TIMEOUT_MS = 90_000

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: DEFAULT_TIMEOUT_MS,
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Rute care necesită sesiune: un 401 pe ele înseamnă token expirat/invalid. */
const PROTECTED_ROUTE_MARKERS = [
  '/auth/me',
  '/profile',
  '/lab-results',
  '/recommendations',
  '/feedback',
  '/foods',
]

/** Handler comun de erori pentru toate instanțele axios: invalidează sesiunea la 401 și normalizează mesajul. */
function handleResponseError(error: unknown): Promise<never> {
  const status = isAxiosError(error) ? error.response?.status : undefined
  const url = isAxiosError(error) ? error.config?.url || '' : ''
  const isProtectedRoute = PROTECTED_ROUTE_MARKERS.some((marker) => url.includes(marker))

  // Login/register întorc 401/400 pentru credențiale greșite: nu sunt sesiuni expirate.
  if (status === 401 && Boolean(getToken()) && isProtectedRoute) {
    clearToken()
  }
  const message = extractErrorMessage(error)
  if (error instanceof Error) {
    error.message = message
  }
  return Promise.reject(error)
}

api.interceptors.response.use(
  (response) => response,
  handleResponseError
)

/** Feedback: timeout dedicat, fără extensia de 120s de la /recommendations. */
const FEEDBACK_HTTP_TIMEOUT_MS = 18_000
const feedbackHttp = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: FEEDBACK_HTTP_TIMEOUT_MS,
})
feedbackHttp.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
feedbackHttp.interceptors.response.use(
  (response) => response,
  handleResponseError
)

export type LabResultsCreatePayload = {
  user_id: number
  notes?: string | null
} & Partial<Record<LabKey, number | null>>

export type AuthSessionResponse = {
  email: string
  fullName: string
  access_token: string
  token_type: string
}

export const authService = {
  login: async (email: string, password: string): Promise<AuthSessionResponse> => {
    const response = await api.post('/auth/login', { email: email.trim(), password })
    return response.data
  },
  register: async (
    email: string,
    password: string,
    fullName: string
  ): Promise<AuthSessionResponse> => {
    const response = await api.post('/auth/register', {
      email: email.trim(),
      password,
      fullName: fullName.trim(),
    })
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export const profileService = {
  create: async (data: Partial<User>) => {
    const response = await api.post('/profile', data)
    return response.data
  },
  getByEmail: async (email: string) => {
    const response = await api.get(`/profile/by-email/${encodeURIComponent(email)}`)
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
  create: async (data: LabResultsCreatePayload) => {
    const response = await api.post('/lab-results', data)
    return response.data
  },
  getByUserId: async (userId: number) => {
    const response = await api.get(`/lab-results/${userId}`)
    return response.data
  },
  extractFromText: async (text: string) => {
    const response = await api.post('/lab-results/extract-from-text', { text })
    return response.data as LabExtractFromApi
  },
}

export type RecommendationsSyncMeta = {
  user_updated_at: string | null
  latest_rec_created_at: string | null
  labs_fresh_at: string | null
  refresh_status?: 'idle' | 'pending' | 'done' | 'failed' | string
  refresh_error?: string | null
  refresh_at?: string | null
  /** Recomandări create înainte de explicațiile pe bază de fapte: se regenerează o singură dată. */
  explanations_outdated?: boolean
}

export const recommendationsService = {
  listStored: async (userId: number) => {
    const response = await api.get(`/recommendations/stored/${userId}`, {
      timeout: REC_STORED_TIMEOUT_MS,
      params: { lang: currentLanguage() },
    })
    return response.data
  },
  getSyncMeta: async (userId: number) => {
    const response = await api.get(`/recommendations/sync-meta/${userId}`, { timeout: 15_000 })
    return response.data as RecommendationsSyncMeta
  },
  startRefreshAsync: async (userId: number, forceRegenerate = false) => {
    const response = await api.post(
      `/recommendations/refresh-async/${userId}?force_regenerate=${forceRegenerate}`,
      {},
      { timeout: 12_000 }
    )
    return response.data as {
      status?: string
      recommendations?: unknown[]
      refresh_status?: string
    }
  },
  materializeSync: async (userId: number, forceRegenerate = false) => {
    const response = await api.post(
      `/recommendations?force_regenerate=${forceRegenerate}&lang=${currentLanguage()}`,
      { user_id: userId },
      { timeout: REC_MATERIALIZE_TIMEOUT_MS }
    )
    return response.data as unknown[]
  },
  replace: async (
    userId: number,
    recommendationId: number,
    options?: { replaceFeedbackRating?: number }
  ) => {
    const body: {
      user_id: number
      replace_recommendation_id: number
      replace_feedback_rating?: number
    } = {
      user_id: userId,
      replace_recommendation_id: recommendationId,
    }
    if (options?.replaceFeedbackRating != null) {
      body.replace_feedback_rating = options.replaceFeedbackRating
    }
    const response = await api.post('/recommendations', body, {
      timeout: REC_REPLACE_TIMEOUT_MS,
      params: { lang: currentLanguage() },
    })
    return response.data
  },
}

export const feedbackService = {
  create: async (data: {
    user_id: number
    recommendation_id: number
    rating: number
    food_id?: number
  }) => {
    const response = await feedbackHttp.post('/feedback', data)
    return response.data
  },
}

export default api
