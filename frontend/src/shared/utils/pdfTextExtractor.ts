/**
 * Extrage textul din fișiere PDF folosind pdfjs-dist.
 * Utilizat pentru rapoarte medicale - extragem textul care va fi apoi parsăt.
 */
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker as string

export async function extractTextFromPdfFile(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer()
  const typedArray = new Uint8Array(arrayBuffer)
  const pdf = await pdfjsLib.getDocument(typedArray).promise
  const numPages = pdf.numPages
  const textParts: string[] = []

  for (let pageNum = 1; pageNum <= numPages; pageNum++) {
    const page = await pdf.getPage(pageNum)
    const textContent = await page.getTextContent()
    const pageText = textContent.items
      .map((item) => ('str' in item ? item.str : ''))
      .join(' ')
    textParts.push(pageText)
  }

  // Unifică paginile; normalizăm spațiile multiple și newline-urile ca spațiu pentru parsing mai bun
  const full = textParts.join('\n')
  return full.replace(/\s+/g, ' ').trim()
}
