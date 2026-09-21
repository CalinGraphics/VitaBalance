/**
 * Export raport recomandări în PDF.
 * Separare clară: date → template → export. Fără logică business aici.
 */
import { pdf } from '@react-pdf/renderer'
import type { PdfLabels, RecommendationForPdf, UserForPdf } from './RecommendationReportDocument'
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

export interface ExportRecommendationPdfParams {
  user: UserForPdf
  recommendations: RecommendationForPdf[]
  /** Limba raportului (implicit RO). Etichetele se traduc; textele explicative generate de server rămân în română. */
  language?: Language
}

/**
 * Generează PDF ca Blob. Poate fi folosit pentru download sau upload.
 */
export async function generateRecommendationPdfBlob(
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
    recommendations,
    generatedAt: formatDate(language),
    labels,
    formatCategory: formatFoodCategory,
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
  link.click()
  URL.revokeObjectURL(url)
}
