import { Info, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

const Disclaimer = () => {
  const { t } = useTranslation()
  const [isVisible, setIsVisible] = useState(true)
  // Pe telefon textul complet ocupă jumătate de ecran: îl arătăm pe două rânduri, cu „Citește tot”.
  const [expanded, setExpanded] = useState(false)

  if (!isVisible) return null

  return (
    <div className="mb-4 w-full min-w-0 sm:mb-6">
      <div
        role="note"
        className="flex w-full items-start gap-3 rounded-card border border-amber-400/25 bg-amber-400/[0.06] px-3.5 py-2.5 sm:px-5 sm:py-3"
      >
        <Info aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300 sm:h-5 sm:w-5" />
        <div className="min-w-0 flex-1">
          <p className={`break-words text-xs leading-relaxed text-amber-100/90 sm:line-clamp-none sm:text-sm ${expanded ? '' : 'line-clamp-2'}`}>
            <strong className="font-semibold text-amber-200">{t('disclaimer.title')}</strong> {t('disclaimer.body')}
          </p>
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
            className="mt-1 min-h-[28px] cursor-pointer text-xs font-semibold text-amber-300 underline-offset-2 hover:underline sm:hidden"
          >
            {expanded ? t('disclaimer.less') : t('disclaimer.more')}
          </button>
        </div>
        <button
          type="button"
          onClick={() => setIsVisible(false)}
          className="-m-1 flex min-h-[44px] min-w-[44px] flex-shrink-0 cursor-pointer items-center justify-center rounded-lg text-amber-300/80 transition-colors hover:bg-white/5 hover:text-amber-100 touch-manipulation"
          aria-label={t('disclaimer.dismiss')}
        >
          <X aria-hidden="true" className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

export default Disclaimer
