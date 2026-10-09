/**
 * Faza 3: schimbarea limbii nu face nicio cerere de rețea și redesenează pagina de recomandări în sub 100 ms.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import i18n from '../../../shared/i18n'
import fixtures from '../explanations/__fixtures__/patients.json'
import type { Recommendation } from '../types'

const recs = (fixtures as unknown as Record<string, Recommendation[]>).p1_male_omnivore

const api = vi.hoisted(() => ({
  listStored: vi.fn(),
  getSyncMeta: vi.fn(),
  startRefreshAsync: vi.fn(),
  materializeSync: vi.fn(),
  replace: vi.fn(),
  feedback: vi.fn(),
}))

vi.mock('../../../services/api', () => ({
  recommendationsService: {
    listStored: api.listStored,
    getSyncMeta: api.getSyncMeta,
    startRefreshAsync: api.startRefreshAsync,
    materializeSync: api.materializeSync,
    replace: api.replace,
  },
  feedbackService: { create: api.feedback },
  default: {},
}))

import Recommendations from './Recommendations'

const user = {
  id: 1, email: 'p1@golden.test', name: 'P1', age: 34, sex: 'M', weight: 79, height: 182,
  activity_level: 'moderate', diet_type: 'omnivore', allergies: '', medical_conditions: '',
}

describe('schimbarea limbii', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    sessionStorage.clear()
    await i18n.changeLanguage('ro')
    api.listStored.mockResolvedValue(recs)
    api.getSyncMeta.mockResolvedValue({
      user_updated_at: '2026-01-01T00:00:00Z',
      latest_rec_created_at: '2026-10-07T00:00:00Z',
      labs_fresh_at: '2026-01-01T00:00:00Z',
      refresh_status: 'idle',
      explanations_outdated: false,
    })
  })

  it('nu face nicio cerere și redesenează în sub 100 ms', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockImplementation(() => Promise.reject(new Error('rețea')))
    const xhrOpen = vi.spyOn(XMLHttpRequest.prototype, 'open')

    const { container } = render(<Recommendations user={user} />)
    const roName = recs[0].food.name_ro
    await waitFor(() => expect(screen.getAllByText(roName).length).toBeGreaterThan(0))
    await waitFor(() => expect(api.getSyncMeta).toHaveBeenCalled())
    // Graficul se încarcă lazy: așteptăm pagina completă, ca măsurătoarea să cuprindă doar schimbarea limbii.
    // (Titlul graficului stă acum în cardul paginii, deci așteptăm chiar graficul, nu titlul.)
    await waitFor(() => expect(container.querySelector('.recharts-responsive-container')).not.toBeNull(), { timeout: 5000 })

    const callsBefore = Object.values(api).map((fn) => fn.mock.calls.length)
    const start = performance.now()
    await act(async () => {
      await i18n.changeLanguage('en')
    })
    const elapsed = performance.now() - start

    expect(screen.getAllByText(recs[0].food.name_en).length).toBeGreaterThan(0)
    expect(screen.queryByText(roName)).toBeNull()
    expect(screen.getAllByText(/below the minimum of 30 ng\/mL/).length).toBeGreaterThan(0)
    expect(Object.values(api).map((fn) => fn.mock.calls.length)).toEqual(callsBefore)
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(xhrOpen).not.toHaveBeenCalled()
    expect(elapsed).toBeLessThan(100)

    fetchSpy.mockRestore()
    xhrOpen.mockRestore()
  })
})
