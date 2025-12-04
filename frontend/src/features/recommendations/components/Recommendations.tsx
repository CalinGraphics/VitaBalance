import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { UtensilsCrossed, Download } from 'lucide-react'
import jsPDF from 'jspdf'
import { GlassCard } from '../../../shared/components'
import { recommendationsService, feedbackService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import NutrientChart from './NutrientChart'

interface Recommendation {
  food_id: number
  food: {
    id: number
    name: string
    category: string
    image_url?: string
  }
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

interface RecommendationsProps {
  user: User
}

const Recommendations = ({ user }: RecommendationsProps) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCard, setExpandedCard] = useState<number | null>(null)

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    try {
      setLoading(true)
      if (user.id) {
        const data = await recommendationsService.get(user.id)
        setRecommendations(data)
      }
    } catch (err) {
      console.error('Eroare la obținerea recomandărilor:', err)
      setError('Nu s-au putut genera recomandări. Vă rugăm să încercați din nou.')
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (recommendationId: number, rating: number): Promise<void> => {
    if (!user.id) {
      throw new Error('User ID is required')
    }
    
    try {
      await feedbackService.create({
        user_id: user.id,
        recommendation_id: recommendationId,
        rating: rating,
        tried: false
      })
    } catch (err) {
      console.error('Eroare la salvarea feedback-ului:', err)
      throw err // Re-throw pentru a permite gestionarea erorilor în componentă
    }
  }

  const exportToPDF = () => {
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })
    
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const marginLeft = 15
    const marginRight = 15
    const marginTop = 20
    const marginBottom = 20
    const contentWidth = pageWidth - marginLeft - marginRight
    
    // Folosim Helvetica (cel mai apropiat de Arial în jsPDF)
    doc.setFont('helvetica')
    
    // Helper function pentru adăugare text cu wrapping corect
    const addText = (text: string, x: number, y: number, options: {
      fontSize?: number
      fontStyle?: 'normal' | 'bold' | 'italic' | 'bolditalic'
      maxWidth?: number
      lineHeight?: number
      color?: [number, number, number]
    } = {}) => {
      const {
        fontSize = 10,
        fontStyle = 'normal',
        maxWidth = contentWidth,
        lineHeight = fontSize * 1.2,
        color = [0, 0, 0]
      } = options
      
      doc.setFontSize(fontSize)
      doc.setFont('helvetica', fontStyle)
      doc.setTextColor(color[0], color[1], color[2])
      
      const lines = doc.splitTextToSize(text, maxWidth)
      doc.text(lines, x, y, {
        maxWidth: maxWidth,
        align: 'left'
      })
      
      return y + (lines.length * lineHeight)
    }
    
    // Helper pentru verificare pagină nouă
    const checkNewPage = (requiredSpace: number) => {
      if (y + requiredSpace > pageHeight - marginBottom) {
        doc.addPage()
        y = marginTop
        return true
      }
      return false
    }
    
    let y = marginTop
    
    // Header
    doc.setFillColor(0, 245, 255)
    doc.rect(0, 0, pageWidth, 35, 'F')
    
    y = addText('VitaBalance', marginLeft, 18, {
      fontSize: 20,
      fontStyle: 'bold',
      color: [0, 0, 0]
    })
    
    y = addText('Recomandări Nutriționale Personalizate', marginLeft, y + 2, {
      fontSize: 12,
      fontStyle: 'normal',
      color: [0, 0, 0]
    })
    
    y = marginTop + 40
    
    // Informații utilizator
    y = addText(`Pentru: ${user.name}`, marginLeft, y, {
      fontSize: 11,
      fontStyle: 'bold'
    })
    
    y = addText(`Data generării: ${new Date().toLocaleDateString('ro-RO', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })}`, marginLeft, y + 4, {
      fontSize: 10,
      fontStyle: 'normal'
    })
    
    y += 8
    
    // Disclaimer
    checkNewPage(15)
    y = addText('⚠️ Aceste recomandări sunt sugestii generale și nu înlocuiesc consultul medical. Consultați întotdeauna un medic sau nutriționist înainte de a face modificări majore în dieta dumneavoastră.', marginLeft, y, {
      fontSize: 9,
      fontStyle: 'normal',
      color: [255, 140, 0],
      maxWidth: contentWidth
    })
    
    y += 10
    
    // Recomandări
    recommendations.forEach((rec, index) => {
      // Verifică dacă mai e spațiu pentru un nou aliment
      checkNewPage(30)
      
      // Titlu aliment
      y = addText(`${index + 1}. ${rec.food.name}`, marginLeft, y, {
        fontSize: 14,
        fontStyle: 'bold',
        color: [0, 150, 200]
      })
      
      y += 5
      
      // Informații de bază
      y = addText(`Categorie: ${rec.food.category}`, marginLeft, y, {
        fontSize: 10,
        fontStyle: 'normal'
      })
      
      y = addText(`Porție sugerată: ${rec.explanation.portion}g`, marginLeft, y + 3, {
        fontSize: 10,
        fontStyle: 'bold'
      })
      
      y = addText(`Acoperă ${rec.coverage.toFixed(1)}% din deficitul nutrițional`, marginLeft, y + 3, {
        fontSize: 10,
        fontStyle: 'bold'
      })
      
      y += 6
      
      // Explicație principală
      checkNewPage(20)
      y = addText(rec.explanation.text, marginLeft, y, {
        fontSize: 10,
        fontStyle: 'normal',
        maxWidth: contentWidth
      })
      
      y += 6
      
      // Motive
      checkNewPage(15)
      y = addText('De ce îl recomand:', marginLeft, y, {
        fontSize: 10,
        fontStyle: 'bold'
      })
      
      y += 4
      rec.explanation.reasons.forEach(reason => {
        checkNewPage(8)
        y = addText(`• ${reason}`, marginLeft + 3, y, {
          fontSize: 10,
          fontStyle: 'normal',
          maxWidth: contentWidth - 3
        })
        y += 1
      })
      
      // Sfaturi
      if (rec.explanation.tips && rec.explanation.tips.length > 0) {
        y += 4
        checkNewPage(15)
        y = addText('Sfaturi:', marginLeft, y, {
          fontSize: 10,
          fontStyle: 'bold'
        })
        
        y += 4
        rec.explanation.tips.forEach(tip => {
          checkNewPage(8)
          y = addText(`• ${tip}`, marginLeft + 3, y, {
            fontSize: 10,
            fontStyle: 'normal',
            maxWidth: contentWidth - 3
          })
          y += 1
        })
      }
      
      // Alternative
      if (rec.explanation.alternatives && rec.explanation.alternatives.length > 0) {
        y += 4
        checkNewPage(10)
        y = addText('Alternative similare:', marginLeft, y, {
          fontSize: 10,
          fontStyle: 'bold'
        })
        
        y += 4
        const alternativesText = rec.explanation.alternatives.join(', ')
        y = addText(alternativesText, marginLeft, y, {
          fontSize: 10,
          fontStyle: 'normal',
          maxWidth: contentWidth
        })
      }
      
      // Linie separator
      y += 8
      if (y > pageHeight - marginBottom - 5) {
        doc.addPage()
        y = marginTop
      }
      doc.setDrawColor(200, 200, 200)
      doc.line(marginLeft, y, pageWidth - marginRight, y)
      y += 8
    })
    
    // Footer pe fiecare pagină
    const totalPages = doc.internal.pages.length - 1
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      doc.setFontSize(8)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(128, 128, 128)
      doc.text(
        `Pagina ${i} din ${totalPages}`,
        pageWidth / 2,
        pageHeight - 8,
        { align: 'center' }
      )
    }
    
    // Nume fișier
    const safeName = user.name.replace(/[^a-zA-Z0-9]/g, '_')
    doc.save(`VitaBalance_Recomandari_${safeName}_${Date.now()}.pdf`)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neonCyan mx-auto mb-4"></div>
          <p className="text-slate-300">Se generează recomandările personalizate...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <GlassCard className="max-w-2xl mx-auto">
        <div className="text-center text-red-400">
          <p>{error}</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <motion.button 
              onClick={fetchRecommendations} 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-neonCyan via-neonPurple to-neonMagenta px-4 py-2 text-sm font-semibold text-slate-950 shadow-neon transition hover:shadow-neon-magenta"
            >
              Încearcă din nou
            </motion.button>
            {recommendations.length > 0 && (
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-4 py-2.5 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 flex items-center gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)]"
              >
                <Download className="w-5 h-5 text-neonCyan" />
                <span>Exportă PDF</span>
              </motion.button>
            )}
          </div>
        </div>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="col-span-2 lg:col-span-3 xl:col-span-3"
        >
          <GlassCard className="w-full max-w-none">
            <div className="flex items-center justify-between mb-6 gap-6">
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-tr from-neonCyan to-neonPurple p-3 rounded-lg shadow-neon">
                  <UtensilsCrossed className="w-6 h-6 text-black" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-slate-100">Recomandările tale</h2>
                  <p className="text-slate-400 text-sm">Alimente personalizate pentru nevoile tale nutriționale</p>
                </div>
              </div>
              <motion.button
                onClick={exportToPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-xl border border-neonCyan/50 bg-gradient-to-r from-slate-800/60 to-slate-900/60 px-5 py-2.5 text-sm font-semibold text-slate-100 hover:bg-gradient-to-r hover:from-slate-700/60 hover:to-slate-800/60 hover:border-neonCyan transition-all duration-200 flex items-center gap-2 shadow-[0_0_15px_rgba(0,245,255,0.3)] hover:shadow-[0_0_25px_rgba(0,245,255,0.5)] whitespace-nowrap"
              >
                <Download className="w-5 h-5 text-neonCyan" />
                <span>Exportă PDF</span>
              </motion.button>
            </div>

            {recommendations.length > 0 && (
              <NutrientChart recommendations={recommendations} />
            )}
          </GlassCard>
        </motion.div>
        {recommendations.map((rec, index) => (
          <RecommendationCard
            key={rec.food_id}
            recommendation={rec}
            index={index}
            isExpanded={expandedCard === rec.food_id}
            onExpand={() => setExpandedCard(expandedCard === rec.food_id ? null : rec.food_id)}
            onFeedback={handleFeedback}
          />
        ))}
      </div>

      {recommendations.length === 0 && (
        <GlassCard className="text-center py-12">
          <p className="text-slate-300 text-lg">
            Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele.
          </p>
        </GlassCard>
      )}
    </div>
  )
}

export default Recommendations

