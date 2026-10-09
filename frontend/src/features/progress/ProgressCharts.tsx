import { useId } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Area, AreaChart, CartesianGrid, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { FlaskConical, Minus, Scale, TrendingDown, TrendingUp, Zap } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { ProgressData, SeriesPoint } from '../../services/api'

// Aceleași culori ca graficul de recomandări (NutrientChart.tsx)
const ACCENT = '#2dd4bf'
const WARN = '#fbbf24'
const AXIS_TEXT = '#a1a1aa'
const GRID = 'rgba(255,255,255,0.08)'
const TOOLTIP_STYLE = { backgroundColor: '#101113', border: '1px solid rgba(255,255,255,0.16)', borderRadius: '10px', color: '#e4e4e7', boxShadow: '0 12px 32px -8px rgba(0,0,0,0.75)' }
const EASE = [0.16, 1, 0.3, 1] as const

function formatDay(iso: string, lang: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(lang === 'en' ? 'en-GB' : 'ro-RO', { day: 'numeric', month: 'short' })
}

/** Pași „rotunzi” pentru axa Y (1, 2, 2.5, 5 × 10^n), ca să nu apară valori ca 12,3 / 13,7. */
function niceTicks(lo: number, hi: number, count = 4): number[] {
  const raw = (hi - lo) / count || 1
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = ([1, 2, 2.5, 5, 10].find((m) => m * mag >= raw) ?? 10) * mag
  const start = Math.floor(lo / step) * step
  const ticks: number[] = []
  for (let v = start; v <= hi + step * 0.5; v += step) ticks.push(Number(v.toFixed(6)))
  return ticks
}

/** Bară de interval: zona sub minim e portocalie, iar markerul alunecă până la valoarea curentă. */
function RangeGauge({ value, low, high, delay }: { value: number; low: number; high: number | null; delay: number }) {
  const top = Math.max(high ?? low * 2, value * 1.15, low * 1.25)
  const pos = Math.min(100, (value / top) * 100)
  const lowPos = (low / top) * 100
  const below = value < low
  return (
    <div aria-hidden="true" className="relative mt-3 h-2 rounded-full bg-white/[0.06]">
      <div className="absolute inset-y-0 left-0 rounded-l-full bg-amber-400/25" style={{ width: `${lowPos}%` }} />
      <div className="absolute inset-y-0 rounded-r-full bg-accent/20" style={{ left: `${lowPos}%`, right: high != null ? `${100 - (high / top) * 100}%` : 0 }} />
      <div className="absolute -top-1 h-4 w-px bg-amber-300/70" style={{ left: `${lowPos}%` }} />
      <motion.div
        className={`absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface ${below ? 'bg-amber-400' : 'bg-accent'}`}
        style={{ boxShadow: `0 0 12px ${below ? WARN : ACCENT}` }}
        initial={{ left: '0%' }}
        animate={{ left: `${pos}%` }}
        transition={{ duration: 1.2, delay, ease: EASE }}
      />
    </div>
  )
}

function MiniChart({ title, points, low, high, unit, lang, minLabel, index, Icon, ceiling }: {
  title: string
  points: SeriesPoint[]
  low?: number | null
  high?: number | null
  unit?: string
  lang: string
  minLabel?: string
  index: number
  Icon: typeof FlaskConical
  /** Valoarea maximă posibilă (energia e 1–5), ca axa să nu treacă de ea. */
  ceiling?: number
}) {
  const { t } = useTranslation()
  const reduce = useReducedMotion()
  const gradientId = `grad-${useId().replace(/:/g, '')}`
  const nf = new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { maximumFractionDigits: 1 })
  const data = points.map((p) => ({ day: formatDay(p.date, lang), value: p.value }))
  const values = points.map((p) => p.value).concat(low != null ? [low] : [])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.2, max * 0.05, 0.5)
  const ticks = niceTicks(Math.max(0, min - pad), ceiling != null ? Math.min(ceiling, max + pad) : max + pad).filter((v) => ceiling == null || v <= ceiling)
  const latest = points[points.length - 1]
  const previous = points.length >= 2 ? points[points.length - 2] : null
  const delta = latest && previous ? latest.value - previous.value : null
  const below = latest != null && low != null && latest.value < low
  const color = below ? WARN : ACCENT
  const delay = Math.min(index, 10) * 0.06
  const TrendIcon = delta == null || Math.abs(delta) < 1e-9 ? Minus : delta > 0 ? TrendingUp : TrendingDown

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: EASE }}
      whileHover={{ y: -2 }}
      className={`group relative overflow-hidden rounded-xl border bg-white/[0.02] p-4 transition-colors ${
        below ? 'border-amber-400/25 hover:border-amber-400/50' : 'border-line hover:border-accent-border'
      }`}
    >
      <div aria-hidden="true" className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100"
        style={{ backgroundColor: `${color}22` }} />
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex min-w-0 gap-2.5">
          <span className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border"
            style={{ borderColor: `${color}55`, backgroundColor: `${color}14`, color }}>
            <Icon aria-hidden="true" className="h-3.5 w-3.5" />
          </span>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-zinc-100">{title}</p>
            {(minLabel || latest) && (
              <p className="mt-0.5 text-xs text-zinc-400">
                {[minLabel, latest ? formatDay(latest.date, lang) : null].filter(Boolean).join(' · ')}
              </p>
            )}
          </div>
        </div>
        {latest && (
          <div className="shrink-0 text-right">
            <p className="text-2xl font-semibold tabular-nums tracking-tight text-zinc-50">
              {nf.format(latest.value)}
              {unit && <span className="ml-1 text-xs font-normal text-zinc-400">{unit}</span>}
            </p>
            {low != null && (
              <span
                className={`mt-1 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
                  below ? 'border-amber-400/40 bg-amber-400/10 text-amber-200' : 'border-accent-border bg-accent/10 text-accent'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${below ? 'bg-amber-300' : 'animate-pulse bg-accent'}`} aria-hidden="true" />
                {below ? t('progress.charts.below') : t('progress.charts.ok')}
              </span>
            )}
          </div>
        )}
      </div>

      {latest && low != null && <RangeGauge value={latest.value} low={low} high={high ?? null} delay={0.2 + delay} />}

      {delta != null && (
        <p className="relative mt-3 flex items-center gap-1.5 text-xs text-zinc-400">
          <TrendIcon aria-hidden="true" className="h-3.5 w-3.5" style={{ color }} />
          {t('progress.charts.delta', { value: `${delta > 0 ? '+' : ''}${nf.format(delta)}${unit ? ` ${unit}` : ''}` })}
        </p>
      )}

      {/* Cu o singură măsurătoare, linia nu spune nimic: rămân valoarea și starea (nota e o dată, deasupra grilei). */}
      {points.length >= 2 && (
        <div className="relative mt-3 h-[160px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.45} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
              <XAxis dataKey="day" stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }} tickLine={false} />
              <YAxis domain={[ticks[0], ceiling ?? ticks[ticks.length - 1]]} ticks={ticks} stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }}
                width={44} tickLine={false} axisLine={false} tickFormatter={(v: number) => nf.format(v)} />
              <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={{ color }} cursor={{ stroke: color, strokeOpacity: 0.4, strokeDasharray: '3 3' }}
                formatter={(v: number) => [`${nf.format(v)} ${unit ?? ''}`.trim(), title]} />
              {low != null && <ReferenceArea y1={ticks[0]} y2={low} fill={WARN} fillOpacity={0.06} ifOverflow="hidden" />}
              {low != null && <ReferenceLine y={low} stroke={WARN} strokeDasharray="4 4" strokeOpacity={0.8} />}
              <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2.5} fill={`url(#${gradientId})`}
                dot={{ r: 3, fill: '#101113', stroke: color, strokeWidth: 2 }}
                activeDot={{ r: 6, fill: color, stroke: '#101113', strokeWidth: 2 }}
                isAnimationActive={!reduce} animationDuration={1400} animationBegin={Math.round((0.2 + delay) * 1000)} animationEasing="ease-out" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </motion.div>
  )
}

const SectionTitle = ({ Icon, children }: { Icon: typeof FlaskConical; children: string }) => (
  <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-zinc-50">
    <Icon aria-hidden="true" className="h-4 w-4 text-accent" />
    {children}
  </h3>
)

/** Graficele de evoluție (recharts), încărcate lazy de ProgressPage. Analizele sub minim apar primele. */
const ProgressCharts = ({ series }: { series: ProgressData['series'] }) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language
  const isBelow = (s: ProgressData['series']['labs'][string]) => s.points.length > 0 && s.points[s.points.length - 1].value < s.low
  const labs = Object.entries(series.labs).sort(([, a], [, b]) => Number(isBelow(b)) - Number(isBelow(a)))
  const fmt = (n: number) => new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { maximumFractionDigits: 1 }).format(n)
  return (
    <div className="space-y-8">
      <div>
        <SectionTitle Icon={FlaskConical}>{t('progress.charts.title')}</SectionTitle>
        {labs.length === 0 ? (
          <p className="text-sm text-zinc-400">{t('progress.charts.empty')}</p>
        ) : (
          <>
            {labs.some(([, s]) => s.points.length < 2) && (
              <p className="mb-4 text-sm text-zinc-400">{t('progress.charts.single')}</p>
            )}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {labs.map(([marker, s], i) => (
                <MiniChart key={marker} index={i} Icon={FlaskConical} title={`${t(`labs.names.${marker}`)} (${s.unit})`} points={s.points}
                  low={s.low} high={s.high} unit={s.unit} lang={lang}
                  minLabel={t('progress.charts.minimum', { value: fmt(s.low), unit: s.unit })} />
              ))}
            </div>
          </>
        )}
      </div>
      <div>
        <SectionTitle Icon={Zap}>{t('progress.charts.wellbeing')}</SectionTitle>
        {series.weight.length === 0 && series.energy.length === 0 ? (
          <p className="text-sm text-zinc-400">{t('progress.charts.wellbeingEmpty')}</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {series.weight.length > 0 && <MiniChart index={0} Icon={Scale} title={t('progress.charts.weight')} points={series.weight} unit="kg" lang={lang} />}
            {series.energy.length > 0 && <MiniChart index={1} Icon={Zap} title={t('progress.charts.energy')} points={series.energy} lang={lang} ceiling={5} />}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProgressCharts
