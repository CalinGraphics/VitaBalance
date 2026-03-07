import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

/** Etichetă Y: centrată vertical, coborâtă, cu distanță față de valori. */
function YAxisLabel(props: { viewBox?: { x?: number; y?: number; width?: number; height?: number } }) {
  const vb = props?.viewBox
  if (!vb || vb.height == null) return null
  const cx = (vb.x ?? 0) - 22
  const cy = (vb.y ?? 0) + (vb.height ?? 0) / 2
  return (
    <text x={cx} y={cy} fill="#e2e8f0" fontSize={13} textAnchor="middle" dominantBaseline="middle" transform={`rotate(-90, ${cx}, ${cy})`}>
      Acoperire (%)
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
  // Calculează datele pentru grafic
  const chartData = recommendations.slice(0, 5).map((rec, index) => ({
    name: rec.food.name.length > 15 ? rec.food.name.substring(0, 15) + '...' : rec.food.name,
    'Acoperire deficit (%)': Math.round(rec.coverage),
    index: index
  }))

  if (chartData.length === 0) return null

  return (
    <div className="mt-6 min-w-0 overflow-hidden">
      <h3 className="text-base sm:text-lg font-semibold text-slate-100 mb-4">
        Comparație acoperire deficit - Top 5 recomandări
      </h3>
      {/* Desktop: height 300, axes 12px; mobile: smaller for readability */}
      <div className="w-full h-[250px] sm:h-[280px] md:h-[300px] overflow-visible">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 12, right: 16, left: 72, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
            <XAxis 
              dataKey="name" 
              angle={-45}
              textAnchor="end"
              height={100}
              fontSize={12}
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis 
              label={<YAxisLabel />}
              domain={[0, 100]}
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              width={40}
              tickMargin={12}
            />
          <Tooltip 
            formatter={(value: number) => [`${value}%`, 'Acoperire deficit']}
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #00f5ff', 
              borderRadius: '8px',
              color: '#e5e7eb'
            }}
            labelStyle={{ color: '#00f5ff' }}
          />
          <Legend 
            wrapperStyle={{ color: '#9ca3af' }}
          />
          <Bar 
            dataKey="Acoperire deficit (%)" 
            fill="url(#neonGradient)"
            radius={[8, 8, 0, 0]}
            barSize={80}
          />
          <defs>
            <linearGradient id="neonGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00f5ff" />
              <stop offset="50%" stopColor="#a855ff" />
              <stop offset="100%" stopColor="#ff007f" />
            </linearGradient>
          </defs>
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  )
}

export default NutrientChart

