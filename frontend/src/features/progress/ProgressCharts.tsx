import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import type { ProgressData, SeriesPoint } from '../../services/api'

// Aceleași culori ca graficul de recomandări (NutrientChart.tsx)
const ACCENT = '#2dd4bf'
const WARN = '#fbbf24'
const AXIS_TEXT = '#a1a1aa'
const GRID = 'rgba(255,255,255,0.08)'
const TOOLTIP_STYLE = { backgroundColor: '#101113', border: '1px solid rgba(255,255,255,0.16)', borderRadius: '8px', color: '#e4e4e7' }

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

function MiniChart({ title, points, low, unit, lang, minLabel }: {
  title: string
  points: SeriesPoint[]
  low?: number | null
  unit?: string
  lang: string
  minLabel?: string
}) {
  const { t } = useTranslation()
  const nf = new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { maximumFractionDigits: 1 })
  const data = points.map((p) => ({ day: formatDay(p.date, lang), value: p.value }))
  const values = points.map((p) => p.value).concat(low != null ? [low] : [])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.2, max * 0.05, 0.5)
  const ticks = niceTicks(Math.max(0, min - pad), max + pad)
  const latest = points[points.length - 1]
  const below = latest != null && low != null && latest.value < low
  return (
    <div className="rounded-lg border border-line bg-white/[0.02] p-4">
      <div className={`flex items-start justify-between gap-3 ${points.length >= 2 ? 'mb-3' : ''}`}>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-zinc-100">{title}</p>
          {(minLabel || latest) && (
            <p className="mt-0.5 text-xs text-zinc-400">
              {[minLabel, latest ? formatDay(latest.date, lang) : null].filter(Boolean).join(' · ')}
            </p>
          )}
        </div>
        {latest && (
          <div className="shrink-0 text-right">
            <p className="text-xl font-semibold tabular-nums text-zinc-50">
              {nf.format(latest.value)}
              {unit && <span className="ml-1 text-xs font-normal text-zinc-400">{unit}</span>}
            </p>
            {low != null && (
              <span
                className={`mt-1 inline-block rounded-full border px-2 py-0.5 text-[11px] font-medium ${
                  below ? 'border-amber-400/40 bg-amber-400/10 text-amber-200' : 'border-accent-border bg-accent/10 text-accent'
                }`}
              >
                {below ? t('progress.charts.below') : t('progress.charts.ok')}
              </span>
            )}
          </div>
        )}
      </div>
      {/* Cu o singură măsurătoare, linia nu spune nimic: rămân valoarea și starea (nota e o dată, deasupra grilei). */}
      {points.length >= 2 && (
        <div className="h-[150px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
              <XAxis dataKey="day" stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }} />
              <YAxis domain={[ticks[0], ticks[ticks.length - 1]]} ticks={ticks} stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }}
                width={44} tickFormatter={(v: number) => nf.format(v)} />
              <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={{ color: ACCENT }}
                formatter={(v: number) => [`${nf.format(v)} ${unit ?? ''}`.trim(), title]} />
              {low != null && <ReferenceLine y={low} stroke={WARN} strokeDasharray="4 4" />}
              <Line type="monotone" dataKey="value" stroke={ACCENT} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

/** Graficele de evoluție (recharts), încărcate lazy de ProgressPage. */
const ProgressCharts = ({ series }: { series: ProgressData['series'] }) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language
  const labs = Object.entries(series.labs)
  const fmt = (n: number) => new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { maximumFractionDigits: 1 }).format(n)
  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-3 text-base font-semibold text-zinc-50">{t('progress.charts.title')}</h3>
        {labs.length === 0 ? (
          <p className="text-sm text-zinc-400">{t('progress.charts.empty')}</p>
        ) : (
          <>
            {labs.some(([, s]) => s.points.length < 2) && (
              <p className="mb-3 text-sm text-zinc-400">{t('progress.charts.single')}</p>
            )}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {labs.map(([marker, s]) => (
                <MiniChart key={marker} title={`${t(`labs.names.${marker}`)} (${s.unit})`} points={s.points} low={s.low}
                  unit={s.unit} lang={lang} minLabel={t('progress.charts.minimum', { value: fmt(s.low), unit: s.unit })} />
              ))}
            </div>
          </>
        )}
      </div>
      <div>
        <h3 className="mb-3 text-base font-semibold text-zinc-50">{t('progress.charts.wellbeing')}</h3>
        {series.weight.length === 0 && series.energy.length === 0 ? (
          <p className="text-sm text-zinc-400">{t('progress.charts.wellbeingEmpty')}</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {series.weight.length > 0 && <MiniChart title={t('progress.charts.weight')} points={series.weight} unit="kg" lang={lang} />}
            {series.energy.length > 0 && <MiniChart title={t('progress.charts.energy')} points={series.energy} lang={lang} />}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProgressCharts
