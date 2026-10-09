import { useId } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { parseOptionalDecimal } from '../../../shared/utils/numberParsing'

interface LabFieldProps {
  label: string
  unit: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  /** Intervalul orientativ; fără el nu se afișează starea. */
  low?: number
  high?: number
}

type Status = 'low' | 'ok' | 'high'

const STATUS_STYLE: Record<Status, { dot: string; text: string; ring: string }> = {
  low: { dot: 'bg-amber-400', text: 'text-amber-200', ring: 'border-amber-400/40 focus-within:border-amber-300/80' },
  ok: { dot: 'bg-accent', text: 'text-accent', ring: 'border-accent-border focus-within:border-accent/80' },
  high: { dot: 'bg-orange-400', text: 'text-orange-200', ring: 'border-orange-400/40 focus-within:border-orange-300/80' },
}

/** Câmp de analiză: unitatea stă în câmp, iar sub el apare, orientativ, dacă valoarea e în interval. */
const LabField = ({ label, unit, value, onChange, placeholder, low, high }: LabFieldProps) => {
  const { t } = useTranslation()
  const id = useId()
  const n = parseOptionalDecimal(value)
  const status: Status | null =
    n === undefined || low === undefined ? null : n < low ? 'low' : high !== undefined && n > high ? 'high' : 'ok'
  const style = status ? STATUS_STYLE[status] : null

  return (
    <div className="mb-2 min-w-0">
      <label htmlFor={id} className="field-label">{label}</label>
      <div
        className={`flex min-h-[44px] items-center rounded-lg border bg-white/[0.03] transition-colors hover:border-line-strong focus-within:bg-white/[0.05] focus-within:ring-2 focus-within:ring-accent/25 ${
          style ? style.ring : 'border-line focus-within:border-accent/70'
        }`}
      >
        <input
          id={id}
          inputMode="decimal"
          pattern="[0-9]*[.,]?[0-9]*"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-describedby={status ? `${id}-status` : undefined}
          className="w-full min-w-0 flex-1 bg-transparent px-3 py-2.5 text-base text-zinc-100 outline-none placeholder:text-zinc-600 sm:text-sm"
        />
        <span className="mr-1.5 flex-shrink-0 rounded-md bg-white/[0.05] px-1.5 py-1 text-[10px] font-medium text-zinc-400 sm:mr-2 sm:px-2 sm:text-[11px]">{unit}</span>
      </div>
      <div className="min-h-[20px]">
        <AnimatePresence mode="wait" initial={false}>
          {status && style && (
            <motion.p
              key={status}
              id={`${id}-status`}
              initial={{ opacity: 0, y: -3 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className={`mt-1 flex items-start gap-1.5 text-[11px] font-medium leading-tight ${style.text}`}
            >
              <span aria-hidden="true" className={`mt-[3px] h-1.5 w-1.5 flex-shrink-0 rounded-full ${style.dot}`} />
              {t(`labs.status.${status}`)}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default LabField
