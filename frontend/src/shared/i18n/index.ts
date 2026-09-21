import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import ro from './locales/ro.json'
import en from './locales/en.json'

export const SUPPORTED_LANGUAGES = ['ro', 'en'] as const
export type Language = (typeof SUPPORTED_LANGUAGES)[number]

export const DEFAULT_LANGUAGE: Language = 'ro'
export const LANGUAGE_STORAGE_KEY = 'vitabalance_lang'

const isSupported = (value: unknown): value is Language =>
  typeof value === 'string' && (SUPPORTED_LANGUAGES as readonly string[]).includes(value)

/** Limba salvată de utilizator; implicit RO. localStorage poate fi indisponibil (mod privat etc.). */
function readStoredLanguage(): Language {
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
    if (isSupported(stored)) return stored
  } catch {
    // ignoră: folosim limba implicită
  }
  return DEFAULT_LANGUAGE
}

i18n.use(initReactI18next).init({
  resources: {
    ro: { translation: ro },
    en: { translation: en },
  },
  lng: readStoredLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES as unknown as string[],
  interpolation: { escapeValue: false }, // React escapează deja
  returnNull: false,
})

const syncDocumentLanguage = (lng: string) => {
  document.documentElement.lang = lng
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lng)
  } catch {
    // ignoră: preferința rămâne doar pe durata sesiunii
  }
}

syncDocumentLanguage(i18n.language)
i18n.on('languageChanged', syncDocumentLanguage)

export const currentLanguage = (): Language => (isSupported(i18n.language) ? i18n.language : DEFAULT_LANGUAGE)

/** Locale BCP-47 pentru formatarea datelor/numerelor. */
export const currentLocale = (): string => (currentLanguage() === 'en' ? 'en-GB' : 'ro-RO')

export default i18n
