import { beforeEach, describe, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import i18n from '../../shared/i18n'
import ro from '../../shared/i18n/locales/ro.json'
import en from '../../shared/i18n/locales/en.json'
import type { ProgressData } from '../../services/api'

const svc = vi.hoisted(() => ({ get: vi.fn(), saveCheckin: vi.fn(), deleteCheckin: vi.fn() }))
vi.mock('../../services/api', () => ({ progressService: svc }))

import ProgressPage from './ProgressPage'

const user = { id: 1, email: 'a@b.ro', name: 'A', age: 30, sex: 'F', weight: 60, height: 165, activity_level: 'moderate', diet_type: 'omnivore' }
const CODES = ['greata', 'varsaturi', 'ameteli', 'oboseala', 'dureri_cap', 'crampe_musculare', 'constipatie', 'diaree', 'balonare', 'arsuri', 'lipsa_poftei']

const progress = (over: Partial<ProgressData> = {}): ProgressData => ({
  storage_available: true,
  symptom_codes: CODES,
  recent_days: 14,
  checkins: [],
  insights: { recent_symptoms: ['oboseala'], lab_suggestions: ['ferritin'], see_doctor: true, see_doctor_reasons: ['severe'], adjustments: ['nausea_lighter_foods'] },
  series: { labs: {}, weight: [], energy: [] },
  ...over,
})

describe('pagina de progres', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await i18n.changeLanguage('ro')
  })

  it('salvează ziua cu stările alese și reîmprospătează recomandările', async () => {
    svc.get.mockResolvedValue(progress())
    svc.saveCheckin.mockResolvedValue({})
    const onChange = vi.fn()
    render(<ProgressPage user={user} onCheckinChange={onChange} />)
    await screen.findByText('Cum te simți azi?')
    fireEvent.click(screen.getByRole('button', { name: 'Greață' }))
    fireEvent.click(screen.getByRole('button', { name: 'Puternic' }))
    fireEvent.click(screen.getByRole('button', { name: '2' }))
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Salvează ziua' }))
    })
    expect(svc.saveCheckin).toHaveBeenCalledWith(expect.objectContaining({ user_id: 1, symptoms: ['greata'], severity: 3, energy: 2 }))
    await waitFor(() => expect(onChange).toHaveBeenCalled())
  })

  it('arată ce înseamnă stările: analize de cerut, consult medical, ajustări', async () => {
    svc.get.mockResolvedValue(progress())
    render(<ProgressPage user={user} />)
    expect(await screen.findByText(/întreabă medicul despre aceste analize: Feritină/)).toBeTruthy()
    expect(screen.getByText('ai raportat o stare puternică.')).toBeTruthy()
    expect(screen.getByText('la greață, alimente mai puțin grase')).toBeTruthy()
  })

  it('anunță când jurnalul nu e încă disponibil (migrarea neaplicată)', async () => {
    svc.get.mockResolvedValue(progress({ storage_available: false }))
    render(<ProgressPage user={user} />)
    expect(await screen.findByText(/va fi disponibil după actualizarea bazei de date/)).toBeTruthy()
    expect(screen.queryByText('Cum te simți azi?')).toBeNull()
  })

  it('cheile de traducere pentru progres sunt aceleași în RO și EN, cu toate simptomele', () => {
    const keys = (o: unknown, prefix = ''): string[] =>
      typeof o === 'object' && o !== null ? Object.entries(o).flatMap(([k, v]) => keys(v, `${prefix}${k}.`)) : [prefix.slice(0, -1)]
    expect(keys(en.progress).sort()).toEqual(keys(ro.progress).sort())
    expect(Object.keys(ro.progress.symptom).sort()).toEqual([...CODES].sort())
  })
})
