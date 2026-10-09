import { describe, expect, it } from 'vitest'
import type { CheckIn, ProgressData } from '../../services/api'
import { lastDays, streak, summarize } from './progressStats'

const END = new Date(2026, 9, 9) // 9 oct. 2026
const day = (iso: string, over: Partial<CheckIn> = {}): CheckIn => ({
  id: Number(iso.replace(/-/g, '')), checked_on: iso, symptoms: [], severity: null, energy: null, weight: null, notes: null, ...over,
})

describe('indicatorii paginii de progres', () => {
  it('ultimele zile se termină azi, în ordine', () => {
    expect(lastDays(3, END)).toEqual(['2026-10-07', '2026-10-08', '2026-10-09'])
  })

  it('seria numără zilele consecutive până azi sau până ieri', () => {
    expect(streak([day('2026-10-09'), day('2026-10-08'), day('2026-10-06')], END)).toBe(2)
    expect(streak([day('2026-10-08'), day('2026-10-07')], END)).toBe(2)
    expect(streak([day('2026-10-05')], END)).toBe(0)
  })

  it('media energiei și analizele în limite folosesc doar ce există', () => {
    const data = {
      checkins: [day('2026-10-09', { energy: 4 }), day('2026-10-08', { energy: 3 }), day('2026-09-01', { energy: 1 })],
      series: {
        labs: {
          ferritin: { unit: 'ng/mL', low: 15, high: null, points: [{ date: '2026-10-01', value: 10 }] },
          vitamin_d: { unit: 'ng/mL', low: 30, high: null, points: [{ date: '2026-10-01', value: 38 }] },
        },
        weight: [],
        energy: [],
      },
    } as unknown as ProgressData
    expect(summarize(data, 14, END)).toEqual({ loggedRecent: 2, streak: 2, avgEnergy: 3.5, labsInRange: 1, labsTotal: 2 })
  })
})
