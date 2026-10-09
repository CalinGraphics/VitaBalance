import { useEffect, useState } from 'react'
import { animate, motion, useReducedMotion } from 'framer-motion'
import { Activity, CalendarDays, Flame, FlaskConical, Zap, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { CheckIn } from '../../services/api'
import { ENERGY_COLORS, lastDays, today, type ProgressSummary } from './progressStats'

/** Număr care urcă de la 0 la valoare (instant când utilizatorul cere mișcare redusă). */
function CountUp({ value, decimals = 0, locale }: { value: number; decimals?: number; locale: string }) {
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? value : 0)
  useEffect(() => {
    if (reduce) {
      setShown(value)
      return
    }
    const controls = animate(0, value, { duration: 1.1, ease: [0.16, 1, 0.3, 1], onUpdate: setShown })
    return () => controls.stop()
  }, [value, reduce])
  return <>{new Intl.NumberFormat(locale, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(shown)}</>
}

function StatTile({ Icon, label, value, suffix, hint, ratio, decimals, locale, index }: {
  Icon: LucideIcon
  label: string
  value: number | null
  suffix?: string
  hint: string
  ratio: number
  decimals?: number
  locale: string
  index: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.08 * index, ease: [0.16, 1, 0.3, 1] }}
      className="group relative overflow-hidden rounded-xl border border-line bg-white/[0.025] p-4 transition-colors hover:border-accent-border"
    >
      <div className="flex items-center gap-2 text-xs font-medium text-zinc-400">
        <Icon aria-hidden="true" className="h-4 w-4 text-accent transition-transform duration-300 group-hover:scale-110" />
        {label}
      </div>
      <p className="mt-2 text-3xl font-semibold tabular-nums tracking-tight text-zinc-50">
        {value == null ? '—' : <CountUp value={value} decimals={decimals} locale={locale} />}
        {value != null && suffix && <span className="ml-1 text-sm font-normal text-zinc-500">{suffix}</span>}
      </p>
      <p className="mt-0.5 text-xs text-zinc-500">{hint}</p>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/[0.06]" aria-hidden="true">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-accent-strong to-accent-hover"
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(Math.min(1, Math.max(0, ratio)) * 100)}%` }}
          transition={{ duration: 1.1, delay: 0.2 + 0.08 * index, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </motion.div>
  )
}

interface ProgressHeroProps {
  summary: ProgressSummary
  checkins: CheckIn[]
  days: number
  selectedDay: string
  onSelectDay: (day: string) => void
  showStrip: boolean
}

/** Antetul paginii: titlu, patru indicatori animați și banda ultimelor zile (alegerea unei zile o deschide în formular). */
const ProgressHero = ({ summary, checkins, days, selectedDay, onSelectDay, showStrip }: ProgressHeroProps) => {
  const { t, i18n } = useTranslation()
  const locale = i18n.language === 'en' ? 'en-GB' : 'ro-RO'
  const byDay = new Map(checkins.map((c) => [c.checked_on, c]))
  const strip = lastDays(days)
  const now = today()

  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="relative w-full overflow-hidden rounded-card border border-line bg-surface shadow-card"
    >
      {/* Lumină de fundal care se mișcă lent, doar în antet */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-24 -top-32 h-80 w-80 animate-aurora rounded-full bg-accent/[0.13] blur-3xl" />
        <div className="absolute -right-16 top-10 h-64 w-64 animate-aurora-slow rounded-full bg-emerald-400/[0.07] blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_at_top_left,black,transparent_70%)]" />
      </div>

      <div className="relative p-5 sm:p-6 md:p-8">
        <div className="flex items-center gap-3.5">
          <motion.div
            initial={{ scale: 0.6, rotate: -12, opacity: 0 }}
            animate={{ scale: 1, rotate: 0, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 260, damping: 18 }}
            className="relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl border border-accent-border bg-accent-soft text-accent"
          >
            <span aria-hidden="true" className="absolute inset-0 animate-ping-slow rounded-xl border border-accent/40" />
            <Activity aria-hidden="true" className="h-6 w-6" />
          </motion.div>
          <div className="min-w-0">
            <h1 className="bg-gradient-to-r from-zinc-50 via-zinc-100 to-accent-hover bg-clip-text text-2xl font-semibold tracking-tight text-transparent sm:text-3xl">
              {t('progress.title')}
            </h1>
            <p className="mt-0.5 text-sm text-zinc-400">{t('progress.subtitle')}</p>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile index={0} Icon={CalendarDays} label={t('progress.stats.logged')} value={summary.loggedRecent} suffix={`/${days}`}
            hint={t('progress.stats.loggedHint', { days })} ratio={summary.loggedRecent / days} locale={locale} />
          <StatTile index={1} Icon={Flame} label={t('progress.stats.streak')} value={summary.streak}
            hint={t('progress.stats.streakHint')} ratio={summary.streak / days} locale={locale} />
          <StatTile index={2} Icon={Zap} label={t('progress.stats.energy')} value={summary.avgEnergy} decimals={1} suffix="/5"
            hint={t('progress.stats.energyHint', { days })} ratio={(summary.avgEnergy ?? 0) / 5} locale={locale} />
          <StatTile index={3} Icon={FlaskConical} label={t('progress.stats.labs')} value={summary.labsTotal ? summary.labsInRange : null}
            suffix={`/${summary.labsTotal}`} hint={t('progress.stats.labsHint', { total: summary.labsTotal })}
            ratio={summary.labsTotal ? summary.labsInRange / summary.labsTotal : 0} locale={locale} />
        </div>

        {showStrip && (
          <div className="mt-6">
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
              <h2 className="text-sm font-semibold text-zinc-100">{t('progress.strip.title', { days })}</h2>
              <p className="text-xs text-zinc-500">{t('progress.strip.hint')}</p>
            </div>
            <div className="grid grid-cols-7 gap-1.5 sm:grid-cols-[repeat(14,minmax(0,1fr))]">
              {strip.map((d, i) => {
                const c = byDay.get(d)
                const date = new Date(`${d}T00:00:00`)
                const selected = d === selectedDay
                const fill = c?.energy != null ? ENERGY_COLORS[c.energy - 1] : c ? '#2dd4bf' : null
                const state = c ? (c.symptoms.length ? t('progress.strip.symptoms') : t('progress.strip.logged')) : t('progress.strip.empty')
                const label = `${date.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' })}: ${state}`
                return (
                  <motion.button
                    key={d}
                    type="button"
                    onClick={() => onSelectDay(d)}
                    aria-pressed={selected}
                    aria-label={label}
                    title={label}
                    initial={{ opacity: 0, y: 10, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    whileHover={{ y: -3 }}
                    whileTap={{ scale: 0.94 }}
                    transition={{ duration: 0.35, delay: 0.25 + i * 0.03 }}
                    className={`relative flex min-h-[64px] cursor-pointer flex-col items-center justify-between rounded-lg border px-1 py-1.5 text-center transition-colors ${
                      selected ? 'border-accent bg-accent-soft' : c ? 'border-line-strong bg-white/[0.03] hover:border-accent-border' : 'border-dashed border-line-strong/70 hover:border-accent-border'
                    }`}
                  >
                    <span className={`text-[10px] font-medium uppercase ${d === now ? 'text-accent' : 'text-zinc-500'}`}>
                      {d === now ? t('progress.strip.today') : date.toLocaleDateString(locale, { weekday: 'short' }).replace('.', '')}
                    </span>
                    <span className={`text-sm font-semibold tabular-nums ${selected ? 'text-accent' : 'text-zinc-200'}`}>{date.getDate()}</span>
                    <span aria-hidden="true" className="flex h-2 items-center gap-0.5">
                      {fill && <span className="h-1.5 w-4 rounded-full" style={{ backgroundColor: fill, boxShadow: `0 0 8px ${fill}80` }} />}
                      {c && c.symptoms.length > 0 && <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />}
                    </span>
                    {selected && (
                      <motion.span layoutId="strip-selected" aria-hidden="true"
                        className="pointer-events-none absolute -inset-px rounded-lg ring-2 ring-accent/60"
                        transition={{ type: 'spring', stiffness: 400, damping: 32 }} />
                    )}
                  </motion.button>
                )
              })}
            </div>
            <div aria-hidden="true" className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-zinc-500">
              <span className="flex items-center gap-1.5">
                <span className="flex gap-0.5">{ENERGY_COLORS.map((col) => <span key={col} className="h-1.5 w-2.5 rounded-full" style={{ backgroundColor: col }} />)}</span>
                {t('progress.checkin.energy')}
              </span>
              <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-amber-400" />{t('progress.strip.symptoms')}</span>
            </div>
          </div>
        )}
      </div>
    </motion.section>
  )
}

export default ProgressHero
