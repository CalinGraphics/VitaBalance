import axios, { isAxiosError } from 'axios'
import type { User } from '../shared/types'
import { extractErrorMessage } from '../shared/utils/apiErrors'
import type { LabExtractFromApi, LabKey } from '../features/medical/utils/labLocalExtract'
import { getToken, clearToken } from './authStorage'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/** Cereri standard (profil, analize, feedback). */
const DEFAULT_TIMEOUT_MS = 45_000
/** POST sincron la /recommendations (ex. înlocuire aliment) poate dura mai mult. */
const LONG_OPERATION_TIMEOUT_MS = 120_000

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
  const url = typeof config.url === 'string' ? config.url : ''
  if (url.includes('/recommendations')) {
    config.timeout = LONG_OPERATION_TIMEOUT_MS
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const status = isAxiosError(error) ? error.response?.status : undefined
    const url = isAxiosError(error) ? error.config?.url || '' : ''
    const hasSession = Boolean(getToken())
    const shouldIgnore401ForAuthFlow =
      url.includes('/auth/verify-magic-link') || url.includes('/auth/request-magic-link')
    const protectedRouteMarkers = [
      '/auth/me',
      '/profile',
      '/lab-results',
      '/recommendations',
      '/feedback',
      '/foods',
    ]
    const isProtectedRoute = protectedRouteMarkers.some((marker) => url.includes(marker))

    if (status === 401 && hasSession && !shouldIgnore401ForAuthFlow && isProtectedRoute) {
      clearToken()
    }
    const message = extractErrorMessage(error)
    if (error instanceof Error) {
      error.message = message
    }
    return Promise.reject(error)
  }
)

export type LabResultsCreatePayload = {
  user_id: number
  notes?: string | null
} & Partial<Record<LabKey, number | null>>

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

export const recommendationsService = {
  /** Citire rapidă din DB (fără regenerare) — pentru afișare imediată înainte de POST. */
  listStored: async (userId: number) => {
    const response = await api.get(`/recommendations/stored/${userId}`)
    return response.data
  },
  /** Pentru polling: compară updated_at profil vs ultima recomandare materializată. */
  getSyncMeta: async (userId: number) => {
    const response = await api.get(`/recommendations/sync-meta/${userId}`, { timeout: 15000 })
    return response.data as {
      user_updated_at: string | null
      latest_rec_created_at: string | null
    }
  },
  /** Pornește regenerarea în background; răspuns rapid (nu așteaptă motorul). */
  startRefreshAsync: async (userId: number, forceRegenerate = false) => {
    const response = await api.post(
      `/recommendations/refresh-async/${userId}?force_regenerate=${forceRegenerate}`,
      {},
      { timeout: 30000 }
    )
    return response.data as { status?: string; recommendations?: unknown[] }
  },
  replace: async (userId: number, recommendationId: number) => {
    const response = await api.post('/recommendations', {
      user_id: userId,
      replace_recommendation_id: recommendationId,
    })
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
