import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { FlaskConical, HeartPulse, Sparkles, Stethoscope, Utensils, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ProgressData } from '../../services/api'

function Row({ Icon, tone = 'accent', index, children }: { Icon: LucideIcon; tone?: 'accent' | 'amber'; index: number; children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.15 + index * 0.08, ease: [0.16, 1, 0.3, 1] }}
      className="flex gap-3"
    >
      <span
        className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border ${
          tone === 'amber' ? 'border-amber-400/30 bg-amber-400/10 text-amber-300' : 'border-accent-border bg-accent-soft text-accent'
        }`}
      >
        <Icon aria-hidden="true" className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1 pt-1">{children}</div>
    </motion.div>
  )
}

/** Ce înseamnă stările din ultimele zile: ajustări, analize de cerut și când e cazul de un medic. */
const InsightsPanel = ({ insights, listFormat }: { insights: ProgressData['insights']; listFormat: (items: string[]) => string }) => {
  const { t } = useTranslation()
  const symptomList = insights.recent_symptoms.map((s) => t(`progress.symptom.${s}`).toLowerCase())
  let i = 0
  return (
    <div className="space-y-4 text-sm text-zinc-300">
      <h3 className="flex items-center gap-2 text-base font-semibold text-zinc-50">
        <Sparkles aria-hidden="true" className="h-4 w-4 text-accent" />
        {t('progress.insights.title')}
      </h3>
      <Row Icon={HeartPulse} index={i++}>
        <p>{symptomList.length ? t('progress.insights.recent', { list: listFormat(symptomList) }) : t('progress.insights.none')}</p>
      </Row>
      {insights.adjustments.length > 0 && (
        <Row Icon={Utensils} index={i++}>
          <p className="font-medium text-zinc-200">{t('progress.insights.adjusted')}</p>
          <ul className="mt-1.5 space-y-1">
            {insights.adjustments.map((id) => (
              <li key={id} className="flex gap-2">
                <span aria-hidden="true" className="mt-2 h-1 w-1 flex-shrink-0 rounded-full bg-accent" />
                {t(`progress.adjustment.${id}`)}
              </li>
            ))}
          </ul>
        </Row>
      )}
      {insights.lab_suggestions.length > 0 && (
        <Row Icon={FlaskConical} index={i++}>
          <p>{t('progress.insights.labs', { list: listFormat(insights.lab_suggestions.map((m) => t(`labs.names.${m}`))) })}</p>
        </Row>
      )}
      {insights.see_doctor && (
        <motion.div
          role="note"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.15 + i * 0.08 }}
          className="relative overflow-hidden rounded-xl border border-amber-400/30 bg-amber-400/[0.06] p-3.5 text-amber-100"
        >
          <span aria-hidden="true" className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-amber-300 to-orange-400" />
          <p className="mb-1 flex items-center gap-2 font-semibold">
            <Stethoscope aria-hidden="true" className="h-4 w-4" />
            {t('progress.insights.doctor')}
          </p>
          <ul className="list-disc space-y-1 pl-5">
            {insights.see_doctor_reasons.map((r) => <li key={r}>{t(`progress.insights.doctorReason.${r}`)}</li>)}
          </ul>
        </motion.div>
      )}
      <p className="border-t border-line pt-3 text-xs text-zinc-500">{t('progress.insights.disclaimer')}</p>
    </div>
  )
}

export default InsightsPanel
