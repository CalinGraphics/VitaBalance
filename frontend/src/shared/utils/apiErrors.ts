import { isAxiosError } from 'axios'
import i18n from '../i18n'

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
 * Backend-ul răspunde cu mesaje în română. Le recunoaștem după conținut și le mapăm pe chei i18n
 * (`apiErrors.<cod>`), ca utilizatorul să vadă eroarea în limba aleasă. Mesajele necunoscute rămân neschimbate.
 */
const KNOWN_API_ERRORS: Array<{ code: string; match: RegExp }> = [
  { code: 'invalidCredentials', match: /email sau parol[aă] incorect/i },
  { code: 'rateLimited', match: /prea multe cereri/i },
  { code: 'emailTaken', match: /deja [iî]nregistrat/i },
  { code: 'emailRequired', match: /^email-ul este obligatoriu/i },
  { code: 'invalidEmail', match: /not a valid email|valid email address/i },
  { code: 'fullNameRequired', match: /numele complet este obligatoriu/i },
  { code: 'passwordRequired', match: /^parola este obligatorie/i },
  { code: 'passwordBlank', match: /doar spa[țt]ii/i },
  { code: 'passwordTooShort', match: /minim 6 caractere/i },
  { code: 'sessionMissing', match: /lipse[șs]te tokenul de autentificare/i },
  { code: 'sessionExpired', match: /token invalid sau expirat/i },
  { code: 'profileNotFound', match: /profilul nu a fost g[aă]sit|utilizatorul nu a fost g[aă]sit/i },
  { code: 'forbidden', match: /nu ai acces|po[țt]i actualiza doar propriul profil/i },
]

/** Codul erorii cunoscute pentru un mesaj brut de la backend, sau `null`. */
export function classifyApiMessage(raw: string): string | null {
  return KNOWN_API_ERRORS.find(({ match }) => match.test(raw))?.code ?? null
}

/** Traduce mesajul dacă e unul cunoscut; altfel îl returnează neschimbat. */
export function localizeApiMessage(raw: string): string {
  const code = classifyApiMessage(raw)
  return code ? i18n.t(`apiErrors.${code}`) : raw
}

function rawErrorMessage(error: unknown): string {
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
    return ''
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return ''
}

/** Cod de eroare cunoscut (vezi `KNOWN_API_ERRORS`) pentru o eroare Axios, sau `null`. */
export function extractErrorCode(error: unknown): string | null {
  return classifyApiMessage(rawErrorMessage(error))
}

/**
 * Mesaj lizibil din eroarea Axios (folosit de interceptorul din `api.ts`), tradus în limba curentă.
 */
export function extractErrorMessage(error: unknown): string {
  const raw = rawErrorMessage(error)
  return raw ? localizeApiMessage(raw) : i18n.t('apiErrors.unexpected')
}

/** Mesaje prietenoase pentru ecranul de recomandări (timeout, gateway, rețea). */
export function humanizeRecommendationClientError(error: unknown): string {
  if (isAxiosError(error) && error.response?.status === 404) {
    return i18n.t('apiErrors.apiRouteMissing')
  }
  const base = extractErrorMessage(error)
  const lower = base.toLowerCase()
  if (lower === 'not found') {
    return i18n.t('apiErrors.apiRouteMissing')
  }
  if (lower.includes('timeout') || lower.includes('exceeded')) {
    return i18n.t('apiErrors.timeout')
  }
  if (lower.includes('network') || lower.includes('econnrefused') || lower.includes('err_network')) {
    return i18n.t('apiErrors.network')
  }
  if (base.includes('504') || lower.includes('gateway')) {
    return i18n.t('apiErrors.gateway')
  }
  if (base.includes('502') || base.includes('503')) {
    return i18n.t('apiErrors.unavailable')
  }
  return base
}
