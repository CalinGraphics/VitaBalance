// Route constants
export const ROUTES = {
  LOGIN: 'login',
  REGISTER: 'register',
  AUTH_VERIFY: 'auth-verify',
  MEDICAL_PROFILE: 'medical-profile',
  LAB_RESULTS: 'lab-results',
  RECOMMENDATIONS: 'recommendations',
  EDIT_PROFILE: 'edit-profile',
} as const

export type RouteType = typeof ROUTES[keyof typeof ROUTES]

