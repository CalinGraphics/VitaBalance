/**
 * Mesajele recomandărilor, construite din fapte reale (motorul backend pe catalogul real, pacienții din
 * backend/tests/golden; regenerare: backend/scripts/export_frontend_fixtures.py).
 */
import { describe, expect, it } from 'vitest'
import '../../../shared/i18n'
import ro from '../../../shared/i18n/locales/ro.json'
import en from '../../../shared/i18n/locales/en.json'
import fixtures from './__fixtures__/patients.json'
import { buildExplanation, TIP_SOURCES, WARNING_SOURCES } from './buildExplanation'
import type { Recommendation } from '../types'

const patients = fixtures as unknown as Record<string, Recommendation[]>
const all = Object.values(patients).flat()
const ROMANIAN_LETTERS = /[ăâîșțĂÂÎȘȚ]/
const CEDILLA = /[şţŞŢ]/
// Reg. (UE) 1924/2006: fără afirmații că un aliment vindecă, tratează sau previne o boală.
const BANNED = /\b(vindec\w*|trateaz\w*|tratament pentru|garant\w*|previn\w*|cure[sd]?|treats?|treatment for|guarantee\w*|prevents?)\b/i

const text = (e: ReturnType<typeof buildExplanation>) =>
  [...e.summary, ...e.nutrients, ...e.why, ...e.tips, ...e.warnings].join(' ')

describe('mesajele recomandărilor', () => {
  it('snapshot RO și EN pentru fiecare pacient-tip', () => {
    for (const [id, recs] of Object.entries(patients)) {
      const rendered = recs.map((r) => ({ ro: buildExplanation(r, 'ro'), en: buildExplanation(r, 'en') }))
      expect(rendered).toMatchSnapshot(id)
    }
  })

  it('nu scrie „ai menționat” / „ne-ai spus” când deficitul vine din analize', () => {
    for (const rec of all) {
      const fromLabs = rec.facts!.nutrients.every((n) => n.need.source !== 'notes')
      if (!fromLabs) continue
      const out = text(buildExplanation(rec, 'ro'))
      expect(out).not.toMatch(/ai menționat|ne-ai spus/i)
      expect(text(buildExplanation(rec, 'en'))).not.toMatch(/you mentioned|you told us/i)
    }
  })

  it('citează valoarea și limba minimă din analize', () => {
    const [first] = patients.p1_male_omnivore
    expect(buildExplanation(first, 'ro').summary.join(' ')).toContain('Vitamina D îți e 18 ng/mL, sub minimul de 30 ng/mL.')
    expect(buildExplanation(first, 'en').summary.join(' ')).toContain('Your vitamin D is 18 ng/mL, below the minimum of 30 ng/mL.')
  })

  it('formulează nevoia din observații ca afirmație a utilizatorului', () => {
    const rec = structuredClone(patients.p1_male_omnivore[0])
    rec.facts!.nutrients = [{ ...rec.facts!.nutrients[0], key: 'magnesium', need: { source: 'notes', severity: 'mild' } }]
    rec.facts!.primary = 'magnesium'
    expect(buildExplanation(rec, 'ro').summary).toContain('Ne-ai spus că ai nevoie de mai mult magneziu.')
    expect(buildExplanation(rec, 'en').summary).toContain('You told us you need more magnesium.')
  })

  it('nu conține afirmații interzise despre boli', () => {
    for (const rec of all) {
      expect(text(buildExplanation(rec, 'ro'))).not.toMatch(BANNED)
      expect(text(buildExplanation(rec, 'en'))).not.toMatch(BANNED)
    }
  })

  it('folosește diacriticele corecte (ș, ț cu virgulă) și engleza nu conține română', () => {
    expect(JSON.stringify(ro)).not.toMatch(CEDILLA)
    for (const rec of all) {
      expect(text(buildExplanation(rec, 'ro'))).not.toMatch(CEDILLA)
      const enText = text(buildExplanation(rec, 'en')).replace(rec.food.name_en, '')
      expect(enText).not.toMatch(ROMANIAN_LETTERS)
    }
  })

  it('fiecare sfat și fiecare atenționare au o sursă', () => {
    expect(Object.keys(TIP_SOURCES).sort()).toEqual(Object.keys(ro.explain.tip).sort())
    expect(Object.keys(WARNING_SOURCES).sort()).toEqual(Object.keys(ro.explain.warning).sort())
    for (const rec of all) {
      const e = buildExplanation(rec, 'ro')
      if (e.tips.length > 1 || e.warnings.length) expect(e.sources.length).toBeGreaterThan(0)
    }
  })

  it('cheile de traducere sunt aceleași în RO și EN', () => {
    const keys = (o: unknown, prefix = ''): string[] =>
      typeof o === 'object' && o !== null
        ? Object.entries(o).flatMap(([k, v]) => keys(v, `${prefix}${k}.`))
        : [prefix.slice(0, -1)]
    expect(keys(en.explain).sort()).toEqual(keys(ro.explain).sort())
    expect(keys(en.foodCategory).sort()).toEqual(keys(ro.foodCategory).sort())
  })

  it('sarcina: atenționare de gătire pentru pește', () => {
    const fish = patients.p3_pregnant_pescatarian.find((r) => r.facts!.category === 'fish')!
    expect(buildExplanation(fish, 'ro').warnings).toContain('Dacă ești însărcinată, mănâncă-l doar bine gătit.')
  })

  it('rândurile vechi, fără fapte, își păstrează textul salvat', () => {
    const legacy = { ...patients.p1_male_omnivore[0], facts: null, legacy: { text: 'Text vechi', reasons: ['r'], tips: [] } }
    const e = buildExplanation(legacy, 'en')
    expect(e.summary).toEqual(['Text vechi'])
    expect(e.why).toEqual(['r'])
  })
})
