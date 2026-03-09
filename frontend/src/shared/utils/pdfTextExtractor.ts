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

  // Unifică paginile. Păstrăm newline-urile între pagini pentru parsing mai bun (tabele/rapoarte),
  // dar normalizăm spațiile ca să evităm token-uri rupte.
  const full = textParts.join('\n')
  return full
    .replace(/[ \t]+/g, ' ')
    .replace(/\n[ \t]+/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
