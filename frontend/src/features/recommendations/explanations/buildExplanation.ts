/**
 * Construiește explicația unei recomandări din FAPTELE trimise de backend (independente de limbă) și din
 * șabloanele ICU din locales/{ro,en}.json (cheile `explain.*`). Schimbarea limbii nu cere nicio cerere la server:
 * se reface doar textul, în browser.
 *
 * Structura mesajului:
 *  1. titlu (ce face alimentul pentru acest utilizator)
 *  2. rezultatul tău (valoarea din analize sau ce ne-ai spus)
 *  3. de ce contează (formulări după mențiunile de sănătate autorizate, Reg. UE 432/2012)
 *  4. ce îți aduce porția
 *  5. cum să-l mănânci (sfaturi cu sursă + o idee de servire)
 *  6. atenționări, când e cazul
 */
import IntlMessageFormat from 'intl-messageformat'
import i18n from '../../../shared/i18n'
import type { Language } from '../../../shared/i18n'
import type { FactNutrient, Recommendation } from '../types'

export interface LocalizedExplanation {
  summary: string[]
  nutrients: string[]
  why: string[]
  tips: string[]
  warnings: string[]
  alternatives: string[]
  sources: string[]
}

/**
 * Sursele sfaturilor de absorbție/preparare. Un sfat fără sursă nu are voie să apară (vezi testele).
 * Ideile de servire (`explain.serve.*`) sunt sugestii culinare, nu afirmații de sănătate.
 */
export const TIP_SOURCES: Record<string, string> = {
  iron: 'Hallberg 1989, Am J Clin Nutr 49:140; Hurrell 1999, Br J Nutr 81:289',
  calcium_iron: 'Hallberg 1991, Am J Clin Nutr 53:112',
  vitamin_d: 'Dawson-Hughes 2015, J Acad Nutr Diet 115:225',
  vitamin_a: 'NIH ODS 2023, Vitamin A fact sheet',
  vitamin_b12_vegan: 'EFSA 2015, EFSA Journal 13(7):4150; NIH ODS 2024, Vitamin B12',
  vitamin_k_anticoagulant: 'NIH ODS 2021, Vitamin K fact sheet',
  zinc: 'Gibson 2010, Food Nutr Bull 31:S134',
  folate: 'McKillop 2002, Br J Nutr 88:681',
  vitamin_c: 'Lee & Kader 2000, Postharvest Biol Technol 20:207',
  iodine: 'WHO 2014, Salt reduction and iodine fortification strategies in public health',
}
export const WARNING_SOURCES: Record<string, string> = {
  pregnancy_cooked: 'NHS 2023, Foods to avoid in pregnancy',
  liver_weekly: 'NHS 2023, Vitamin A',
  raw_fresh: 'FDA 2020, Food safety for people with weakened immune systems',
}
export const CLAIMS_SOURCE = 'Reg. (UE) 432/2012'

const MAX_SOURCED_TIPS = 2

const LOCALES: Record<Language, string> = { ro: 'ro-RO', en: 'en-GB' }
const formatterCache = new Map<string, IntlMessageFormat>()

function message(lang: Language, key: string, values: Record<string, string | number> = {}): string {
  const cacheKey = `${lang}:${key}`
  let fmt = formatterCache.get(cacheKey)
  if (!fmt) {
    const raw = i18n.getResource(lang, 'translation', `explain.${key}`)
    if (typeof raw !== 'string') return ''
    fmt = new IntlMessageFormat(raw, LOCALES[lang])
    formatterCache.set(cacheKey, fmt)
  }
  return String(fmt.format(values))
}

function has(lang: Language, key: string): boolean {
  return typeof i18n.getResource(lang, 'translation', `explain.${key}`) === 'string'
}

export function formatNumber(lang: Language, value: number): string {
  return new Intl.NumberFormat(LOCALES[lang], { maximumFractionDigits: 1 }).format(value)
}

function joinList(lang: Language, items: string[]): string {
  return new Intl.ListFormat(LOCALES[lang], { style: 'long', type: 'conjunction' }).format(items)
}

function capitalize(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s
}

export function foodName(rec: Pick<Recommendation, 'food'>, lang: Language): string {
  const f = rec.food
  return (lang === 'en' ? f.name_en : f.name_ro) || f.name_ro || f.name_en || ''
}

function nutrientName(lang: Language, key: string): string {
  return message(lang, `nutrient.${key}`) || key
}

function share(lang: Language, n: FactNutrient): string {
  return message(lang, 'share', { pct: n.pct, nutrient: nutrientName(lang, n.key) })
}

export function buildExplanation(rec: Recommendation, lang: Language): LocalizedExplanation {
  const out: LocalizedExplanation = { summary: [], nutrients: [], why: [], tips: [], warnings: [], alternatives: [], sources: [] }
  const facts = rec.facts
  if (!facts) {
    // Rând vechi, fără fapte: textul salvat (RO) până la regenerare.
    const legacy = rec.legacy
    if (legacy?.text) out.summary.push(legacy.text)
    out.why.push(...(legacy?.reasons ?? []))
    out.tips.push(...(legacy?.tips ?? []))
    return out
  }

  const food = foodName(rec, lang)
  const nutrients = facts.nutrients ?? []
  const primary = nutrients.find((n) => n.key === facts.primary) ?? nutrients[0]
  const needs = nutrients.filter((n) => n.need?.source === 'lab' || n.need?.source === 'notes')
  const diet = facts.profile?.diet ?? null
  const conditions = facts.profile?.conditions ?? []

  // 1. Titlu
  if (primary && needs.length > 0) {
    const fortifiedB12 = primary.key === 'vitamin_b12' && diet === 'vegan' && facts.category === 'plant_milks'
    out.summary.push(message(lang, fortifiedB12 ? 'headline.vitamin_b12_vegan' : `headline.${primary.key}`, { food }))
  } else if (nutrients.length > 0) {
    out.summary.push(message(lang, 'headline.general', { food, list: joinList(lang, nutrients.map((n) => share(lang, n))) }))
  }

  // 2. Rezultatul tău — formularea depinde de sursa nevoii; „ne-ai spus” doar pentru observații.
  for (const n of needs) {
    const need = n.need
    if (need.source === 'lab' && need.marker && has(lang, `result.lab.${need.marker}`)) {
      out.summary.push(
        message(lang, `result.lab.${need.marker}`, {
          value: formatNumber(lang, need.value ?? 0),
          threshold: formatNumber(lang, need.threshold ?? 0),
          unit: need.unit ?? '',
        }) + ' ' + message(lang, 'result.severity', { severity: need.severity ?? 'mild' })
      )
    } else if (need.source === 'notes') {
      out.summary.push(message(lang, `result.notes.${n.key}`))
    }
  }

  // 3. De ce contează (doar pentru nutrientul principal al unei nevoi)
  if (primary && needs.length > 0 && has(lang, `why.${primary.key}`)) {
    out.why.push(message(lang, `why.${primary.key}`))
    out.sources.push(CLAIMS_SOURCE)
  }
  if (diet) out.why.push(message(lang, 'considered.diet', { diet }))
  const allergies = facts.profile?.allergies ?? []
  if (allergies.length > 0) {
    const labels = allergies.map((a) => i18n.t(`allergies.${a}.label`, { lng: lang }).toLowerCase())
    out.why.push(message(lang, 'considered.allergies', { list: joinList(lang, labels) }))
  }
  for (const c of conditions) {
    if (has(lang, `condition.${c}.label`)) {
      out.why.push(
        message(lang, 'considered.condition', {
          condition: message(lang, `condition.${c}.label`),
          restriction: message(lang, `condition.${c}.restriction`),
        })
      )
    }
  }
  const adjustments = facts.symptom_adjustments ?? []
  if (adjustments.length > 0) {
    const labels = adjustments.map((id) => i18n.t(`progress.adjustment.${id}`, { lng: lang }))
    out.why.push(message(lang, 'considered.symptoms', { list: joinList(lang, labels) }))
  }
  if (!facts.has_lab_data) out.why.push(message(lang, 'considered.no_labs'))

  // 4. Ce îți aduce porția
  if (primary) {
    const label = (lang === 'en' ? facts.portion?.label_en : facts.portion?.label_ro) ?? `${facts.portion?.amount ?? ''} ${facts.portion?.unit ?? 'g'}`
    out.nutrients.push(
      message(lang, 'portion', {
        portion: capitalize(label),
        pct: primary.pct,
        full: primary.pct >= 100 ? 'yes' : 'no',
        nutrient: nutrientName(lang, primary.key),
      })
    )
    const others = nutrients.filter((n) => n !== primary)
    if (others.length > 0) out.nutrients.push(message(lang, 'also', { list: joinList(lang, others.map((n) => share(lang, n))) }))
  }

  // 5. Cum să-l mănânci: sfaturi cu sursă (după nutrienți și profil) + o idee de servire
  const tipKeys: string[] = []
  const nutrientKeys = nutrients.map((n) => n.key)
  const needKeys = new Set(needs.map((n) => n.key))
  for (const key of nutrientKeys) {
    if (key === 'vitamin_b12' && diet === 'vegan') tipKeys.push('vitamin_b12_vegan')
    else if (key === 'iron' && facts.animal) continue // vitamina C ajută fierul din plante (non-hem)
    else if (TIP_SOURCES[key]) tipKeys.push(key)
  }
  if (nutrientKeys.includes('calcium') && needKeys.has('iron')) tipKeys.push('calcium_iron')
  if (conditions.includes('anticoagulant') && facts.category === 'leafy_greens') tipKeys.unshift('vitamin_k_anticoagulant')
  for (const key of [...new Set(tipKeys)].slice(0, MAX_SOURCED_TIPS)) {
    out.tips.push(message(lang, `tip.${key}`))
    out.sources.push(TIP_SOURCES[key])
  }
  // La alimentele crude de origine animală nu dăm idei de gătit (ar contrazice consumul crud).
  if (facts.category && !facts.flags?.includes('raw_animal') && has(lang, `serve.${facts.category}`))
    out.tips.push(message(lang, `serve.${facts.category}`))

  // 6. Atenționări
  const warnings: string[] = []
  if (conditions.includes('pregnancy') && ['fish', 'shellfish', 'eggs', 'meat', 'poultry'].includes(facts.category ?? ''))
    warnings.push('pregnancy_cooked')
  if (facts.flags?.includes('liver')) warnings.push('liver_weekly')
  if (facts.flags?.includes('raw_animal')) warnings.push('raw_fresh')
  for (const w of warnings) {
    out.warnings.push(message(lang, `warning.${w}`))
    out.sources.push(WARNING_SOURCES[w])
  }

  out.alternatives = (rec.alternatives ?? []).map((a) => (lang === 'en' ? a.name_en : a.name_ro) || a.name_ro)
  out.sources = [...new Set(out.sources)]
  return out
}

export function sourcesLine(lang: Language, sources: string[]): string {
  return sources.length ? message(lang, 'sources', { list: sources.join('; ') }) : ''
}

export function categoryLabel(rec: Pick<Recommendation, 'food'>, lang: Language, fallback: (c: string) => string): string {
  const key = rec.food.category_key
  if (key) {
    const label = i18n.getResource(lang, 'translation', `foodCategory.${key}`)
    if (typeof label === 'string') return label
  }
  return fallback(rec.food.category)
}
