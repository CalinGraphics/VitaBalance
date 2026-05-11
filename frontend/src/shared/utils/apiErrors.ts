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

/** Mesaje prietenoase pentru ecranul de recomandări (timeout, gateway, rețea). */
export function humanizeRecommendationClientError(error: unknown): string {
  const base = extractErrorMessage(error)
  const lower = base.toLowerCase()
  if (lower.includes('timeout') || lower.includes('exceeded')) {
    return 'Serverul a răspuns prea lent (timeout). Reîncearcă sau verifică conexiunea; recomandările se regenerează după modificarea profilului.'
  }
  if (lower.includes('network') || lower.includes('econnrefused') || lower.includes('err_network')) {
    return 'Nu s-a putut contacta serverul. Verifică dacă API-ul rulează și conexiunea la internet.'
  }
  if (base.includes('504') || lower.includes('gateway')) {
    return 'Gateway timeout (504): proxy-ul sau hosting-ul a întrerupt cererea prea devreme. Mărește timeout-ul la proxy sau reîncearcă.'
  }
  if (base.includes('502') || base.includes('503')) {
    return 'Server temporar indisponibil (502/503). Reîncearcă peste câteva momente.'
  }
  return base
}
