import { motion } from 'framer-motion'
import { Download, LayoutGrid, Trophy, UtensilsCrossed, type LucideIcon } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { CountUp, HeroBackdrop } from '../../../shared/components'
import type { User } from '../../../shared/types'
import UserProfileInfo from './UserProfileInfo'

const EASE = [0.16, 1, 0.3, 1] as const

function Tile({ Icon, label, hint, index, children }: { Icon: LucideIcon; label: string; hint: string; index: number; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.1 + 0.08 * index, ease: EASE }}
      className="group min-w-0 rounded-xl border border-line bg-white/[0.025] p-4 transition-colors hover:border-accent-border"
    >
      <p className="flex items-center gap-2 text-xs font-medium text-zinc-400">
        <Icon aria-hidden="true" className="h-4 w-4 text-accent transition-transform duration-300 group-hover:scale-110" />
        {label}
      </p>
      <div className="mt-2 truncate text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">{children}</div>
      <p className="mt-0.5 text-xs leading-snug text-zinc-500">{hint}</p>
    </motion.div>
  )
}

interface RecommendationsHeroProps {
  user: User
  count: number
  categories: number
  bestName: string | null
  onExport?: () => void
}

/** Antetul paginii de recomandări: titlu, profilul pe scurt, trei indicatori și exportul PDF. */
const RecommendationsHero = ({ user, count, categories, bestName, onExport }: RecommendationsHeroProps) => {
  const { t, i18n } = useTranslation()
  const locale = i18n.language === 'en' ? 'en-GB' : 'ro-RO'
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="relative w-full overflow-hidden rounded-card border border-line bg-surface shadow-card"
    >
      <HeroBackdrop />
      <div className="relative p-5 sm:p-6 md:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3.5">
            <motion.div
              initial={{ scale: 0.6, rotate: -12, opacity: 0 }}
              animate={{ scale: 1, rotate: 0, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 260, damping: 18 }}
              className="relative flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl border border-accent-border bg-accent-soft text-accent"
            >
              <span aria-hidden="true" className="absolute inset-0 animate-ping-slow rounded-xl border border-accent/40" />
              <UtensilsCrossed aria-hidden="true" className="h-6 w-6" />
            </motion.div>
            <div className="min-w-0">
              <h1 className="bg-gradient-to-r from-zinc-50 via-zinc-100 to-accent-hover bg-clip-text text-2xl font-semibold tracking-tight text-transparent sm:text-3xl">
                {t('recommendations.title')}
              </h1>
              <p className="mt-0.5 text-sm text-zinc-400">{t('recommendations.subtitle')}</p>
            </div>
          </div>
          {onExport && (
            <motion.button
              type="button"
              onClick={onExport}
              whileHover={{ y: -2 }}
              whileTap={{ scale: 0.97 }}
              className="flex min-h-[44px] cursor-pointer items-center justify-center gap-2 self-start whitespace-nowrap rounded-lg border border-accent-border bg-accent-soft px-4 text-sm font-semibold text-accent transition-colors hover:bg-accent/20 touch-manipulation sm:self-center"
            >
              <Download aria-hidden="true" className="h-4 w-4 flex-shrink-0" />
              <span>{t('recommendations.exportPdf')}</span>
            </motion.button>
          )}
        </div>

        <div className="mt-5">
          <UserProfileInfo user={user} />
        </div>

        {count > 0 && (
          <div className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-3">
            <Tile index={0} Icon={UtensilsCrossed} label={t('recommendations.stats.foods')} hint={t('recommendations.stats.foodsHint')}>
              <CountUp value={count} locale={locale} />
            </Tile>
            <Tile index={1} Icon={LayoutGrid} label={t('recommendations.stats.categories')} hint={t('recommendations.stats.categoriesHint')}>
              <CountUp value={categories} locale={locale} />
            </Tile>
            {bestName && (
              <div className="col-span-2 md:col-span-1">
                <Tile index={2} Icon={Trophy} label={t('recommendations.stats.best')} hint={t('recommendations.stats.bestHint')}>
                  <span className="bg-gradient-to-r from-accent to-emerald-200 bg-clip-text text-transparent" title={bestName}>{bestName}</span>
                </Tile>
              </div>
            )}
          </div>
        )}
      </div>
    </motion.section>
  )
}

export default RecommendationsHero
