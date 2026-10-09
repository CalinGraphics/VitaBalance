import type { CheckIn, ProgressData } from '../../services/api'

/** Data locală ca `YYYY-MM-DD` (formatul din jurnal). */
export const isoDay = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

export const today = () => isoDay(new Date())

/** Energie 1–5: de la portocaliu (epuizat) la accentul teal (plin de energie). */
export const ENERGY_COLORS = ['#fb923c', '#fbbf24', '#a3e635', '#34d399', '#2dd4bf'] as const

/** Ultimele `count` zile, de la cea mai veche la azi. */
export function lastDays(count: number, end = new Date()): string[] {
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(end.getFullYear(), end.getMonth(), end.getDate() - (count - 1 - i))
    return isoDay(d)
  })
}

/** Zile consecutive notate, terminate azi sau ieri (azi încă poate fi completat). */
export function streak(checkins: CheckIn[], end = new Date()): number {
  const logged = new Set(checkins.map((c) => c.checked_on))
  const cursor = new Date(end.getFullYear(), end.getMonth(), end.getDate())
  if (!logged.has(isoDay(cursor))) cursor.setDate(cursor.getDate() - 1)
  let n = 0
  while (logged.has(isoDay(cursor))) {
    n += 1
    cursor.setDate(cursor.getDate() - 1)
  }
  return n
}

export interface ProgressSummary {
  loggedRecent: number
  streak: number
  avgEnergy: number | null
  labsInRange: number
  labsTotal: number
}

export function summarize(data: ProgressData, days: number, end = new Date()): ProgressSummary {
  const window = new Set(lastDays(days, end))
  const recent = data.checkins.filter((c) => window.has(c.checked_on))
  const energies = recent.map((c) => c.energy).filter((e): e is number => e != null)
  const labs = Object.values(data.series.labs).filter((s) => s.points.length > 0)
  return {
    loggedRecent: recent.length,
    streak: streak(data.checkins, end),
    avgEnergy: energies.length ? energies.reduce((a, b) => a + b, 0) / energies.length : null,
    labsInRange: labs.filter((s) => s.points[s.points.length - 1].value >= s.low).length,
    labsTotal: labs.length,
  }
}
