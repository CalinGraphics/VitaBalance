import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList, Cell } from 'recharts'
import { useReducedMotion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { foodName } from '../explanations/buildExplanation'
import type { Recommendation } from '../types'

// Culori de grafic: o singură culoare de accent, text/grilă neutre (aliniate cu tokenii din tailwind.config.js)
const ACCENT = '#2dd4bf'
const AXIS_TEXT = '#a1a1aa'
const GRID = 'rgba(255,255,255,0.08)'

/** Etichetă Y: centrată vertical, coborâtă, cu distanță față de valori. */
function YAxisLabel(props: { viewBox?: { x?: number; y?: number; width?: number; height?: number }; text: string }) {
  const vb = props?.viewBox
  if (!vb || vb.height == null) return null
  const cx = (vb.x ?? 0) - 22
  const cy = (vb.y ?? 0) + (vb.height ?? 0) / 2
  return (
    <text x={cx} y={cy} fill={AXIS_TEXT} fontSize={13} textAnchor="middle" dominantBaseline="middle" transform={`rotate(-90, ${cx}, ${cy})`}>
      {props.text}
    </text>
  )
}

interface NutrientChartProps {
  recommendations: Recommendation[]
  /** Aceeași „potrivire” ca pe carduri (scorul raportat la primul aliment), deci barele scad în ordinea listei. */
  matchPctOf: (rec: Recommendation) => number
}

const NutrientChart = ({ recommendations, matchPctOf }: NutrientChartProps) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language === 'en' ? 'en' : 'ro'
  const seriesName = t('recommendations.chart.series')
  // Pe telefon, marginea mare pentru eticheta axei Y lua o parte prea mare din lățime.
  const [narrow, setNarrow] = useState(() => typeof window !== 'undefined' && window.innerWidth < 640)
  useEffect(() => {
    const onResize = () => setNarrow(window.innerWidth < 640)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  // Primele 5 din lista primită (ordinea backend-ului = ordinea cardurilor).
  const chartData = recommendations.slice(0, 5).map((rec) => {
    const name = foodName(rec, lang)
    return {
      name: name.length > 18 ? name.substring(0, 18) + '…' : name,
      fullName: name,
      match: matchPctOf(rec),
      coverage: Math.round(rec.coverage),
    }
  })

  const reduce = useReducedMotion()
  if (chartData.length === 0) return null

  return (
    <div className="mt-4 min-w-0 overflow-hidden">
      <div className="h-[250px] w-full overflow-visible sm:h-[280px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 28, right: narrow ? 4 : 16, left: narrow ? 28 : 72, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
            <XAxis
              dataKey="name"
              angle={-45}
              textAnchor="end"
              height={100}
              fontSize={12}
              stroke={GRID}
              tick={{ fill: AXIS_TEXT, fontSize: 12 }}
            />
            <YAxis
              label={narrow ? undefined : <YAxisLabel text={t('recommendations.chart.yAxis')} />}
              domain={[0, 100]}
              stroke={GRID}
              tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              width={narrow ? 32 : 40}
              tickMargin={narrow ? 6 : 12}
              unit={narrow ? '%' : undefined}
            />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.04)' }}
              formatter={(value: number) => [`${value}%`, seriesName]}
              labelFormatter={(_label, payload) => {
                const row = payload?.[0]?.payload
                return row ? `${row.fullName} · ${t('recommendations.chart.coverage', { pct: row.coverage })}` : _label
              }}
              contentStyle={{
                backgroundColor: '#101113',
                border: '1px solid rgba(255,255,255,0.16)',
                borderRadius: '8px',
                color: '#e4e4e7',
              }}
              labelStyle={{ color: ACCENT }}
            />
            <defs>
              <linearGradient id="match-bar" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#5eead4" stopOpacity={1} />
                <stop offset="100%" stopColor="#0d9488" stopOpacity={0.55} />
              </linearGradient>
            </defs>
            <Bar dataKey="match" name={seriesName} fill="url(#match-bar)" radius={[8, 8, 0, 0]} maxBarSize={56}
              isAnimationActive={!reduce} animationDuration={1100} animationEasing="ease-out">
              {/* Primul aliment (100%) e evidențiat; restul păstrează gradientul. */}
              {chartData.map((row, i) => (
                <Cell key={row.fullName} fill="url(#match-bar)" fillOpacity={i === 0 ? 1 : 0.8} />
              ))}
              <LabelList dataKey="match" position="top" offset={8} formatter={(v: number) => `${v}%`}
                style={{ fill: '#e4e4e7', fontSize: 12, fontWeight: 600 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default NutrientChart
