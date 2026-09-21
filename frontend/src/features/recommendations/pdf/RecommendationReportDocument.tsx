/**
 * Template PDF pentru raportul de recomandări.
 * Doar prezentare – fără logică business. Primește datele gata pregătite.
 * Textul este normalizat fără diacritice (ă,â,î,ș,ț) pentru compatibilitate font PDF.
 * Etichetele vin traduse din exterior (`labels`), deoarece randarea PDF nu are acces la contextul React i18n.
 */
import React from 'react'
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
} from '@react-pdf/renderer'

/** Înlocuiește diacriticele românești pentru afișare corectă în PDF (font Helvetica). */
function faraDiacritice(s: string): string {
  if (!s || typeof s !== 'string') return ''
  const map: Record<string, string> = {
    ă: 'a', â: 'a', î: 'i', ș: 's', ț: 't',
    Ă: 'A', Â: 'A', Î: 'I', Ș: 'S', Ț: 'T',
  }
  return s.replace(/[ăâîșțĂÂÎȘȚ]/g, (c) => map[c] ?? c)
}

/** Scoate toate aparițiile [context: ...] sau (context: ...) din text. */
function faraPrefixContext(s: string): string {
  if (!s || typeof s !== 'string') return ''
  return s
    .replace(/\s*\[context:\s*[^\]]*\]\s*/gi, ' ')
    .replace(/\s*\(context:\s*[^)]*\)\s*/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function normalizeSentenceEnd(s: string): string {
  const t = (s || '').trim()
  if (!t) return ''
  return /[.!?]$/.test(t) ? t : `${t}.`
}

export interface RecommendationForPdf {
  food_id: number
  food: { id: number; name: string; category: string }
  score: number
  coverage: number
  explanation: {
    text: string
    portion: number
    portion_unit?: 'g' | 'ml' | string
    reasons: string[]
    tips?: string[]
    alternatives?: string[]
  }
  recommendation_id: number
}

export interface UserForPdf {
  name?: string
  email?: string
  id?: number
}

const styles = StyleSheet.create({
  page: {
    padding: 30,
    fontFamily: 'Helvetica',
    fontSize: 10,
  },
  header: {
    backgroundColor: '#0d9488',
    padding: 15,
    marginBottom: 20,
  },
  headerTitle: {
    color: '#fff',
    fontSize: 22,
    textAlign: 'center',
    marginBottom: 4,
  },
  headerSubtitle: {
    color: '#fff',
    fontSize: 11,
    textAlign: 'center',
  },
  userBox: {
    backgroundColor: '#f0fdfa',
    padding: 12,
    borderRadius: 4,
    marginBottom: 12,
  },
  userLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  disclaimer: {
    backgroundColor: '#fff8dc',
    padding: 10,
    borderRadius: 4,
    marginBottom: 16,
    fontSize: 9,
    color: '#644a00',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#0f766e',
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#0d9488',
    paddingBottom: 4,
  },
  recommendationBlock: {
    marginBottom: 16,
  },
  foodName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#0f766e',
    marginBottom: 4,
  },
  meta: {
    flexDirection: 'row',
    marginBottom: 6,
    fontSize: 9,
    color: '#333',
  },
  metaItem: {
    marginRight: 16,
  },
  explanationLabel: {
    fontWeight: 'bold',
    marginBottom: 2,
    fontSize: 9,
  },
  explanationText: {
    fontSize: 9,
    color: '#333',
    marginBottom: 4,
    lineHeight: 1.4,
  },
  footer: {
    position: 'absolute',
    bottom: 20,
    left: 30,
    right: 30,
    borderTopWidth: 0.5,
    borderTopColor: '#ccc',
    paddingTop: 8,
    fontSize: 8,
    color: '#777',
    textAlign: 'center',
  },
})

/** Texte statice ale raportului, în limba aleasă de utilizator (`pdf.*` din traduceri). */
export interface PdfLabels {
  subtitle: string
  beneficiary: string
  defaultUser: string
  generatedAt: string
  important: string
  disclaimer: string
  section: string
  category: string
  portion: string
  coverage: string
  description: string
  motivation: string
  rights: string
}

interface RecommendationReportDocumentProps {
  user: UserForPdf
  recommendations: RecommendationForPdf[]
  generatedAt: string
  labels: PdfLabels
  /** Categoria alimentului, deja tradusă. */
  formatCategory: (category: string) => string
}

export const RecommendationReportDocument: React.FC<RecommendationReportDocumentProps> = ({
  user,
  recommendations,
  generatedAt,
  labels,
  formatCategory,
}) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>VitaBalance</Text>
        <Text style={styles.headerSubtitle}>{faraDiacritice(labels.subtitle)}</Text>
      </View>

      <View style={styles.userBox}>
        <Text style={styles.userLabel}>{labels.beneficiary}: {faraDiacritice(user.name || labels.defaultUser)}</Text>
        <Text style={{ fontSize: 9, color: '#555' }}>{labels.generatedAt}: {generatedAt}</Text>
      </View>

      <View style={styles.disclaimer}>
        <Text style={{ fontWeight: 'bold', marginBottom: 2 }}>{faraDiacritice(labels.important)}</Text>
        <Text>{faraDiacritice(labels.disclaimer)}</Text>
      </View>

      <Text style={styles.sectionTitle}>{faraDiacritice(labels.section)}</Text>

      {recommendations.map((rec, index) => {
        const descriere = faraDiacritice(
          faraPrefixContext(rec.explanation.text.replace(/\n\n---\n\n/g, '\n\n'))
        )
        const motive = (rec.explanation.reasons || [])
          .map((r) => normalizeSentenceEnd(faraDiacritice(faraPrefixContext(r))))
          .filter(Boolean)
        return (
          <View key={rec.recommendation_id} style={styles.recommendationBlock} wrap={false}>
            <Text style={styles.foodName}>
              {index + 1}. {faraDiacritice(rec.food.name)}
            </Text>
            <View style={styles.meta}>
              <Text style={styles.metaItem}>{labels.category}: {faraDiacritice(formatCategory(rec.food.category))}</Text>
              <Text style={styles.metaItem}>
                {labels.portion}:{' '}
                {rec.explanation.portion_unit === 'ml'
                  ? `${rec.explanation.portion} ml`
                  : `${rec.explanation.portion} g`}
              </Text>
              <Text style={styles.metaItem}>{labels.coverage}: {rec.coverage.toFixed(1)}%</Text>
            </View>
            <Text style={styles.explanationLabel}>{labels.description}:</Text>
            <Text style={styles.explanationText}>{descriere}</Text>
            {motive.length > 0 && (
              <>
                <Text style={styles.explanationLabel}>{labels.motivation}:</Text>
                <Text style={styles.explanationText}>{motive.join(' ')}</Text>
              </>
            )}
          </View>
        )
      })}

      <View style={styles.footer} fixed>
        <Text>
          VitaBalance © {new Date().getFullYear()}. {faraDiacritice(labels.rights)}
        </Text>
      </View>
    </Page>
  </Document>
)
