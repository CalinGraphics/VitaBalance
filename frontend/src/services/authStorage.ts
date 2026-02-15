/**
 * Persistență token JWT – localStorage. Folosit pentru auth la fiecare request.
 */
const TOKEN_KEY = 'vitabalance_access_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}
