import axios from 'axios'
import type { User } from '../shared/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API Services
export const profileService = {
  create: async (data: Partial<User>) => {
    const response = await api.post('/profile', data)
    return response.data
  },
}

export const labResultsService = {
  create: async (data: any) => {
    const response = await api.post('/lab-results', data)
    return response.data
  },
}

export const recommendationsService = {
  get: async (userId: number) => {
    const response = await api.post('/recommendations', { user_id: userId })
    return response.data
  },
}

export const feedbackService = {
  create: async (data: { user_id: number; recommendation_id: number; rating: number; tried: boolean }) => {
    const response = await api.post('/feedback', data)
    return response.data
  },
}

export default api

