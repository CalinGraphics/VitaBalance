// Route constants
export const ROUTES = {
  LOGIN: 'login',
  REGISTER: 'register',
  MEDICAL_PROFILE: 'medical-profile',
  LAB_RESULTS: 'lab-results',
  RECOMMENDATIONS: 'recommendations',
} as const

export type RouteType = typeof ROUTES[keyof typeof ROUTES]

