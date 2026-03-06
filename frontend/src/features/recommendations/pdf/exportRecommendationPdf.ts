/**
 * Export raport recomandări în PDF.
 * Separare clară: date → template → export. Fără logică business aici.
 */
import { pdf } from '@react-pdf/renderer'
import type { RecommendationForPdf, UserForPdf } from './RecommendationReportDocument'
import { RecommendationReportDocument } from './RecommendationReportDocument'
import React from 'react'

const formatDate = () =>
  new Date().toLocaleDateString('ro-RO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

export interface ExportRecommendationPdfParams {
  user: UserForPdf
  recommendations: RecommendationForPdf[]
}

/**
 * Generează PDF ca Blob. Poate fi folosit pentru download sau upload.
 */
export async function generateRecommendationPdfBlob(
  params: ExportRecommendationPdfParams
): Promise<Blob> {
  const { user, recommendations } = params
  const doc = React.createElement(RecommendationReportDocument, {
    user,
    recommendations,
    generatedAt: formatDate(),
  })
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
  const safeName = (params.user.name || 'Utilizator').replace(/[^a-zA-Z0-9]/g, '_')
  link.download = filename || `VitaBalance_Recomandari_${safeName}_${Date.now()}.pdf`
  link.click()
  URL.revokeObjectURL(url)
}
