import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES, currentLanguage, type Language } from '../../i18n'

/** Selector RO/EN, mereu vizibil în header; alegerea se salvează în localStorage (vezi shared/i18n). */
const LanguageSwitcher = () => {
  const { t, i18n } = useTranslation()
  const active = currentLanguage()

  const change = (lng: Language) => {
    if (lng !== active) void i18n.changeLanguage(lng)
  }

  return (
    <div
      role="group"
      aria-label={t('lang.label')}
      className="flex items-center rounded-lg border border-line bg-white/[0.03] p-0.5"
    >
      {SUPPORTED_LANGUAGES.map((lng) => {
        const isActive = lng === active
        return (
          <button
            key={lng}
            type="button"
            lang={lng}
            onClick={() => change(lng)}
            aria-pressed={isActive}
            aria-label={t('lang.switchTo', { language: t(`lang.${lng}`) })}
            title={t(`lang.${lng}`)}
            className={`min-h-[36px] min-w-[40px] cursor-pointer rounded-md px-2.5 text-xs font-semibold uppercase tracking-wide transition-colors touch-manipulation ${
              isActive ? 'bg-white/10 text-zinc-50' : 'text-zinc-400 hover:text-zinc-100'
            }`}
          >
            {lng}
          </button>
        )
      })}
    </div>
  )
}

export default LanguageSwitcher
