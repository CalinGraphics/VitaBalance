/**
 * Template PDF pentru raportul de recomandări.
 * Doar prezentare – fără logică business. Primește datele gata pregătite.
 * Textul este normalizat fără diacritice (ă,â,î,ș,ț) pentru compatibilitate font PDF.
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
  food: { id: number; name: string; category: string; image_url?: string }
  score: number
  coverage: number
  explanation: {
    text: string
    portion: number
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
    backgroundColor: '#0096c8',
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
    backgroundColor: '#f0f8ff',
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
    color: '#006494',
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#0096c8',
    paddingBottom: 4,
  },
  recommendationBlock: {
    marginBottom: 16,
  },
  foodName: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#006494',
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

const DISCLAIMER = faraDiacritice(
  'Aceste recomandări sunt sugestii generale bazate pe informațiile furnizate și nu înlocuiesc consultul medical profesional. Consultați un medic sau nutriționist autorizat înainte de modificări majore în dietă.'
)

interface RecommendationReportDocumentProps {
  user: UserForPdf
  recommendations: RecommendationForPdf[]
  generatedAt: string
}

export const RecommendationReportDocument: React.FC<RecommendationReportDocumentProps> = ({
  user,
  recommendations,
  generatedAt,
}) => (
  <Document>
    <Page size="A4" style={styles.page}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>VitaBalance</Text>
        <Text style={styles.headerSubtitle}>{faraDiacritice('Raport de Recomandări Nutriționale Personalizate')}</Text>
      </View>

      <View style={styles.userBox}>
        <Text style={styles.userLabel}>Beneficiar: {faraDiacritice(user.name || 'Utilizator')}</Text>
        <Text style={{ fontSize: 9, color: '#555' }}>Data generarii: {generatedAt}</Text>
      </View>

      <View style={styles.disclaimer}>
        <Text style={{ fontWeight: 'bold', marginBottom: 2 }}>IMPORTANT:</Text>
        <Text>{DISCLAIMER}</Text>
      </View>

      <Text style={styles.sectionTitle}>{faraDiacritice('RECOMANDĂRI NUTRIȚIONALE')}</Text>

      {recommendations.map((rec, index) => {
        const descriere = faraDiacritice(faraPrefixContext(rec.explanation.text))
        const motive = (rec.explanation.reasons || [])
          .map((r) => normalizeSentenceEnd(faraDiacritice(faraPrefixContext(r))))
          .filter(Boolean)
        return (
          <View key={rec.recommendation_id} style={styles.recommendationBlock} wrap={false}>
            <Text style={styles.foodName}>
              {index + 1}. {faraDiacritice(rec.food.name)}
            </Text>
            <View style={styles.meta}>
              <Text style={styles.metaItem}>Categorie: {faraDiacritice(rec.food.category)}</Text>
              <Text style={styles.metaItem}>Portie sugerata: {rec.explanation.portion}g</Text>
              <Text style={styles.metaItem}>Acoperire deficit: {rec.coverage.toFixed(1)}%</Text>
            </View>
            <Text style={styles.explanationLabel}>Descriere:</Text>
            <Text style={styles.explanationText}>{descriere}</Text>
            {motive.length > 0 && (
              <>
                <Text style={styles.explanationLabel}>Motivatie:</Text>
                <Text style={styles.explanationText}>{motive.join(' ')}</Text>
              </>
            )}
          </View>
        )
      })}

      <View style={styles.footer} fixed>
        <Text>
          VitaBalance © {new Date().getFullYear()}. {faraDiacritice('Toate drepturile rezervate.')}
        </Text>
      </View>
    </Page>
  </Document>
)
