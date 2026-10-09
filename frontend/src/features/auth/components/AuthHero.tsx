import type { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Activity, FlaskConical, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const EASE = [0.16, 1, 0.3, 1] as const

// Ce face aplicația, pe scurt (doar pe desktop, unde coloana are loc).
const POINTS = [
  { key: 'labs', Icon: FlaskConical },
  { key: 'data', Icon: ShieldCheck },
  { key: 'progress', Icon: Activity },
] as const

const STEPS = ['profile', 'labs', 'recs'] as const

/** Previzualizare decorativă a aplicației: o analiză care urcă în limite și potrivirea unui aliment. */
function PreviewCards() {
  const { t } = useTranslation()
  return (
    <div aria-hidden="true" className="relative mt-10 hidden h-48 md:block">
      <motion.div
        initial={{ opacity: 0, y: 16, rotate: -2 }}
        animate={{ opacity: 1, y: 0, rotate: -2 }}
        transition={{ duration: 0.7, delay: 0.5, ease: EASE }}
        className="absolute left-0 top-0 w-64 animate-float rounded-xl border border-line-strong bg-surface/90 p-4 shadow-pop backdrop-blur"
      >
        <div className="flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-zinc-200">
            <FlaskConical className="h-3.5 w-3.5 text-accent" />
            {t('labs.names.vitamin_d')}
          </p>
          <span className="rounded-full border border-accent-border bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent">
            {t('progress.charts.ok')}
          </span>
        </div>
        <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-50">
          33 <span className="text-xs font-normal text-zinc-500">ng/mL</span>
        </p>
        <svg viewBox="0 0 220 48" className="mt-1 h-12 w-full">
          <defs>
            <linearGradient id="auth-spark" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1="0" x2="220" y1="22" y2="22" stroke="#fbbf24" strokeOpacity="0.5" strokeDasharray="4 4" />
          <motion.path
            d="M0 40 C 40 38, 60 34, 90 30 S 150 20, 220 8 L 220 48 L 0 48 Z"
            fill="url(#auth-spark)"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 1.4 }}
          />
          <motion.path
            d="M0 40 C 40 38, 60 34, 90 30 S 150 20, 220 8"
            fill="none"
            stroke="#2dd4bf"
            strokeWidth="2.5"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1.4, delay: 0.8, ease: 'easeInOut' }}
          />
        </svg>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16, rotate: 3 }}
        animate={{ opacity: 1, y: 0, rotate: 3 }}
        transition={{ duration: 0.7, delay: 0.7, ease: EASE }}
        className="absolute left-48 top-20 w-56 rounded-xl border border-line-strong bg-surface/90 p-4 shadow-pop backdrop-blur [animation-delay:-3s] animate-float"
      >
        <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-zinc-400">
          <Sparkles className="h-3.5 w-3.5 text-accent" />
          {t('recommendations.card.match')}
        </p>
        <div className="mt-3 flex items-center gap-2">
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-accent-strong to-accent-hover"
              initial={{ width: 0 }}
              animate={{ width: '92%' }}
              transition={{ duration: 1.2, delay: 1.1, ease: EASE }}
            />
          </div>
          <span className="flex items-center gap-1 text-sm font-semibold tabular-nums text-accent">
            <TrendingUp className="h-3.5 w-3.5" />
            92%
          </span>
        </div>
      </motion.div>
    </div>
  )
}

interface AuthHeroProps {
  eyebrow: string
  title: ReactNode
  text: string
  align: 'left' | 'right'
  /** Lista de avantaje și previzualizarea (doar pe pagina de autentificare). */
  showcase?: boolean
  /** Pașii de după înregistrare (doar pe pagina de cont nou). */
  steps?: boolean
}

/** Coloana de prezentare de lângă formularele de autentificare și înregistrare. */
const AuthHero = ({ eyebrow, title, text, align, showcase = false, steps = false }: AuthHeroProps) => {
  const { t } = useTranslation()
  const side = align === 'left' ? 'md:text-left' : 'md:text-right'
  return (
    <div className={`w-full max-w-sm text-center ${side}`}>
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className={`mb-3 inline-flex items-center gap-2 rounded-full border border-accent-border bg-accent-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent`}
      >
        <span className="relative flex h-1.5 w-1.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-70" />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
        </span>
        {eyebrow}
      </motion.p>
      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.08, ease: EASE }}
        className="mb-3 text-3xl font-semibold tracking-tight text-zinc-50 sm:text-4xl md:text-5xl md:leading-[1.08]"
      >
        {title}
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.16, ease: EASE }}
        className="text-base leading-relaxed text-zinc-400"
      >
        {text}
      </motion.p>
      {steps && (
        <ol className="mt-8 hidden space-y-4 md:block">
          {STEPS.map((key, i) => (
            <motion.li
              key={key}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.25 + i * 0.1, ease: EASE }}
              className="flex flex-row-reverse items-center gap-3 text-sm text-zinc-300"
            >
              <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm font-bold tabular-nums ${
                i === STEPS.length - 1 ? 'border-transparent bg-gradient-to-br from-accent-hover to-accent-strong text-accent-fg shadow-[0_0_16px_rgba(45,212,191,0.45)]' : 'border-accent-border bg-accent/10 text-accent'
              }`}>
                {i + 1}
              </span>
              {t(`auth.register.steps.${key}`)}
            </motion.li>
          ))}
        </ol>
      )}
      {showcase && (
        <>
          <ul className="mt-7 hidden space-y-3 md:block">
            {POINTS.map(({ key, Icon }, i) => (
              <motion.li
                key={key}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.25 + i * 0.08, ease: EASE }}
                className="group flex items-center gap-3 text-sm text-zinc-300"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-accent-border bg-accent/10 transition-transform duration-300 group-hover:scale-110 group-hover:bg-accent/20">
                  <Icon aria-hidden="true" className="h-4 w-4 text-accent" />
                </span>
                {t(`auth.login.points.${key}`)}
              </motion.li>
            ))}
          </ul>
          <PreviewCards />
        </>
      )}
    </div>
  )
}

/** Numele aplicației cu un gradient care curge încet. */
export const BrandName = () => (
  <span className="animate-shimmer bg-gradient-to-r from-accent via-emerald-200 to-accent bg-[length:200%_auto] bg-clip-text text-transparent">
    VitaBalance
  </span>
)

/** Cardul formularului, cu un halou teal discret în spate. */
export const AuthCardGlow = ({ children }: { children: ReactNode }) => (
  <div className="relative w-full max-w-full md:max-w-md">
    <div aria-hidden="true" className="pointer-events-none absolute -inset-6 -z-10 rounded-[28px] bg-accent/[0.07] blur-2xl" />
    <div aria-hidden="true" className="pointer-events-none absolute -inset-px rounded-card bg-gradient-to-br from-accent/40 via-transparent to-transparent opacity-80" />
    {children}
  </div>
)

export default AuthHero
