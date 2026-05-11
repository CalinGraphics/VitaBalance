import { isAxiosError } from 'axios'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/**
 * Formatează câmpul `detail` din răspunsurile FastAPI/Pydantic (string, listă sau obiect).
 */
export function formatApiDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (isRecord(item)) {
          const msg = typeof item.msg === 'string' ? item.msg : ''
          const loc = Array.isArray(item.loc) ? item.loc.map(String).join('.') : ''
          return loc && msg ? `${loc}: ${msg}` : msg || JSON.stringify(item)
        }
        return JSON.stringify(item)
      })
      .join('; ')
  }
  if (isRecord(detail)) {
    if (typeof detail.msg === 'string') return detail.msg
    if (typeof detail.message === 'string') return detail.message
    return JSON.stringify(detail)
  }
  return ''
}

/**
 * Mesaj lizibil din eroarea Axios (folosit de interceptorul din `api.ts`).
 */
export function extractErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const data = error.response?.data
    if (isRecord(data) && 'detail' in data) {
      const formatted = formatApiDetail(data.detail)
      if (formatted) return formatted
    }
    if (isRecord(data) && typeof data.message === 'string') {
      return data.message
    }
    if (error.message) return error.message
    return 'A apărut o eroare neașteptată'
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'A apărut o eroare neașteptată'
}
