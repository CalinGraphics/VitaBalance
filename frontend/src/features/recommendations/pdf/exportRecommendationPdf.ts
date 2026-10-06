/**
 * Export raport recomandări în PDF.
 * Separare clară: date → template → export. Fără logică business aici.
 */
import { pdf } from '@react-pdf/renderer'
import type { PdfLabels, RecommendationForPdf, UserForPdf } from './RecommendationReportDocument'
import type { Recommendation } from '../types'
import { buildExplanation, categoryLabel, foodName } from '../explanations/buildExplanation'
import { RecommendationReportDocument } from './RecommendationReportDocument'
import React, { type ReactElement } from 'react'
import i18n, { DEFAULT_LANGUAGE, type Language } from '../../../shared/i18n'
import { formatFoodCategory } from '../../../shared/utils/formatters'

const LOCALES: Record<Language, string> = { ro: 'ro-RO', en: 'en-GB' }

const formatDate = (language: Language) =>
  new Date().toLocaleDateString(LOCALES[language], {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

interface ExportRecommendationPdfParams {
  user: UserForPdf
  recommendations: Recommendation[]
  /** Limba raportului (implicit RO): etichetele și explicațiile se construiesc în această limbă. */
  language?: Language
}

function toPdfItem(rec: Recommendation, language: Language): RecommendationForPdf {
  const e = buildExplanation(rec, language)
  const portion = rec.facts ? `${rec.facts.portion.amount} ${rec.facts.portion.unit === 'ml' ? 'ml' : 'g'}` : '—'
  return {
    recommendation_id: rec.recommendation_id,
    name: foodName(rec, language),
    category: categoryLabel(rec, language, formatFoodCategory),
    portion,
    coverage: rec.coverage,
    description: [...e.summary, ...e.nutrients],
    motivation: [...e.why, ...e.warnings],
  }
}

/**
 * Generează PDF ca Blob. Poate fi folosit pentru download sau upload.
 */
async function generateRecommendationPdfBlob(
  params: ExportRecommendationPdfParams
): Promise<Blob> {
  const { user, recommendations, language = DEFAULT_LANGUAGE } = params
  const t = i18n.getFixedT(language)
  const labels: PdfLabels = {
    subtitle: t('pdf.subtitle'),
    beneficiary: t('pdf.beneficiary'),
    defaultUser: t('pdf.defaultUser'),
    generatedAt: t('pdf.generatedAt'),
    important: t('pdf.important'),
    disclaimer: t('pdf.disclaimer'),
    section: t('pdf.section'),
    category: t('pdf.category'),
    portion: t('pdf.portion'),
    coverage: t('pdf.coverage'),
    description: t('pdf.description'),
    motivation: t('pdf.motivation'),
    rights: t('pdf.rights'),
  }
  const doc = React.createElement(RecommendationReportDocument, {
    user,
    recommendations: recommendations.map((r) => toPdfItem(r, language)),
    generatedAt: formatDate(language),
    labels,
  }) as ReactElement
  const blob = await pdf(doc).toBlob()
  return blob
}

/**
 * Generează PDF și declanșează descărcarea în browser.
 */
export async function downloadRecommendationPdf(
  params: ExportRecommendationPdfParams,
  filename?: string
): Promise<void> {
  const blob = await generateRecommendationPdfBlob(params)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  const safeName = (params.user.name || i18n.t('pdf.defaultUser')).replace(/[^a-zA-Z0-9]/g, '_')
  link.download = filename || `VitaBalance_${i18n.t('pdf.fileName')}_${safeName}_${Date.now()}.pdf`
  // Firefox ignoră click-ul pe un link care nu e în document.
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Revocat imediat, URL-ul dispare înainte ca browserul să citească fișierul și descărcarea e anulată.
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
