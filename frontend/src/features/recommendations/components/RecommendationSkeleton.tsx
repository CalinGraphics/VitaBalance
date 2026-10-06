import { GlassCard } from '../../../shared/components'

const bar = 'animate-pulse rounded bg-white/[0.07]'

/** Schelet pentru grafic, cât timp se încarcă modulul lui (React.lazy). */
export function ChartSkeleton() {
  return <div aria-hidden="true" className={`mt-6 h-[250px] w-full sm:h-[280px] md:h-[300px] ${bar}`} />
}

/** Schelet pentru lista de recomandări la prima încărcare: arată forma paginii în locul unui spinner. */
const RecommendationSkeleton = ({ label }: { label: string }) => (
  <div role="status" aria-live="polite" aria-busy="true">
    <span className="sr-only">{label}</span>
    <div className="grid grid-cols-1 items-stretch gap-4 sm:gap-6 md:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <GlassCard key={i} className="flex min-h-[440px] flex-col gap-4">
          <div className={`h-6 w-2/3 ${bar}`} />
          <div className={`h-4 w-1/3 ${bar}`} />
          <div className={`h-2.5 w-full ${bar}`} />
          <div className={`h-24 w-full ${bar}`} />
          <div className={`h-4 w-5/6 ${bar}`} />
          <div className={`h-4 w-4/6 ${bar}`} />
        </GlassCard>
      ))}
    </div>
  </div>
)

export default RecommendationSkeleton
