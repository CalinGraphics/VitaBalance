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

function MiniChart({ title, points, low, unit, lang, minLabel }: {
  title: string
  points: SeriesPoint[]
  low?: number | null
  unit?: string
  lang: string
  minLabel?: string
}) {
  const data = points.map((p) => ({ day: formatDay(p.date, lang), value: p.value }))
  const values = points.map((p) => p.value).concat(low != null ? [low] : [])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const pad = Math.max((max - min) * 0.2, max * 0.05, 0.5)
  return (
    <div className="rounded-lg border border-line bg-white/[0.02] p-3">
      <p className="mb-1 text-sm font-semibold text-zinc-100">{title}</p>
      {minLabel && <p className="mb-2 text-xs text-amber-200/80">{minLabel}</p>}
      <div className="h-[160px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
            <XAxis dataKey="day" stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }} />
            <YAxis domain={[Math.max(0, min - pad), max + pad]} stroke={GRID} tick={{ fill: AXIS_TEXT, fontSize: 11 }}
              width={44} tickFormatter={(v: number) => new Intl.NumberFormat(lang === 'en' ? 'en-GB' : 'ro-RO', { maximumFractionDigits: 1 }).format(v)} />
            <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={{ color: ACCENT }}
              formatter={(v: number) => [`${v} ${unit ?? ''}`.trim(), title]} />
            {low != null && <ReferenceLine y={low} stroke={WARN} strokeDasharray="4 4" />}
            <Line type="monotone" dataKey="value" stroke={ACCENT} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
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
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {labs.map(([marker, s]) => (
              <MiniChart key={marker} title={`${t(`labs.names.${marker}`)} (${s.unit})`} points={s.points} low={s.low}
                unit={s.unit} lang={lang} minLabel={t('progress.charts.minimum', { value: fmt(s.low), unit: s.unit })} />
            ))}
          </div>
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
