/**
 * Sesiunea Supabase Auth (access + refresh token) – localStorage. Folosită pentru auth la fiecare request.
 */
const TOKEN_KEY = 'vitabalance_access_token'
const REFRESH_KEY = 'vitabalance_refresh_token'

export type StoredSession = {
  access_token: string
  refresh_token?: string | null
}

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export function getToken(): string | null {
  return read(TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return read(REFRESH_KEY)
}

export function setSession(session: StoredSession): void {
  try {
    localStorage.setItem(TOKEN_KEY, session.access_token)
    if (session.refresh_token) localStorage.setItem(REFRESH_KEY, session.refresh_token)
  } catch {
    // stocare indisponibilă (mod privat): sesiunea rămâne doar pentru pagina curentă
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  } catch {
    // ignorat
  }
}
