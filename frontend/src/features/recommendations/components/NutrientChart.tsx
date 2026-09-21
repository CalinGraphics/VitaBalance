import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useTranslation } from 'react-i18next'

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
  recommendations: Array<{
    food: { name: string }
    explanation: { portion: number }
    coverage: number
  }>
}

const NutrientChart = ({ recommendations }: NutrientChartProps) => {
  const { t } = useTranslation()
  const seriesName = t('recommendations.chart.series')

  const chartData = recommendations.slice(0, 5).map((rec) => ({
    name: rec.food.name.length > 15 ? rec.food.name.substring(0, 15) + '...' : rec.food.name,
    coverage: Math.round(rec.coverage),
  }))

  if (chartData.length === 0) return null

  return (
    <div className="mt-6 min-w-0 overflow-hidden">
      <h3 className="mb-4 text-base font-semibold text-zinc-100 sm:text-lg">{t('recommendations.chart.title')}</h3>
      <div className="h-[250px] w-full overflow-visible sm:h-[280px] md:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 16, left: 72, bottom: 8 }}>
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
              label={<YAxisLabel text={t('recommendations.chart.yAxis')} />}
              domain={[0, 100]}
              stroke={GRID}
              tick={{ fill: AXIS_TEXT, fontSize: 12 }}
              width={40}
              tickMargin={12}
            />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.04)' }}
              formatter={(value: number) => [`${value}%`, seriesName]}
              contentStyle={{
                backgroundColor: '#101113',
                border: '1px solid rgba(255,255,255,0.16)',
                borderRadius: '8px',
                color: '#e4e4e7',
              }}
              labelStyle={{ color: ACCENT }}
            />
            <Bar dataKey="coverage" name={seriesName} fill={ACCENT} radius={[6, 6, 0, 0]} maxBarSize={56} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default NutrientChart
