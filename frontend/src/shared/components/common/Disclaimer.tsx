import { Info, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

const Disclaimer = () => {
  const { t } = useTranslation()
  const [isVisible, setIsVisible] = useState(true)

  if (!isVisible) return null

  return (
    <div className="mb-6 w-full min-w-0">
      <div
        role="note"
        className="flex w-full items-start gap-3 rounded-card border border-amber-400/25 bg-amber-400/[0.06] px-4 py-3 sm:px-5"
      >
        <Info aria-hidden="true" className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-300" />
        <p className="min-w-0 flex-1 break-words text-sm leading-relaxed text-amber-100/90">
          <strong className="font-semibold text-amber-200">{t('disclaimer.title')}</strong> {t('disclaimer.body')}
        </p>
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
