import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { UtensilsCrossed, Download } from 'lucide-react'
import jsPDF from 'jspdf'
import { GlassCard } from '../../../shared/components'
import { recommendationsService } from '../../../services/api'
import type { User } from '../../../shared/types'
import RecommendationCard from './RecommendationCard'
import NutrientChart from './NutrientChart'
import UserProfileInfo from './UserProfileInfo'

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
  // Debug logging only in development
  if (import.meta.env.DEV) {
    console.log('Recommendations component render - user:', user)
  }
  
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRecommendations()
  }, [])

<<<<<<< Updated upstream
  const fetchRecommendations = async () => {
=======
    if (hasChanged) {
      // Regenerează recomandările dacă s-au schimbat criteriile
      fetchRecommendations(true)
      setPrevUserValues({
        diet_type: user.diet_type,
        activity_level: user.activity_level,
        allergies: user.allergies,
        medical_conditions: user.medical_conditions
      })
    } else {
      // Altfel, doar încarcă recomandările existente
      fetchRecommendations(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id, user.diet_type, user.activity_level, user.allergies, user.medical_conditions])

  const fetchRecommendations = async (forceRegenerate: boolean = false) => {
>>>>>>> Stashed changes
    try {
      if (import.meta.env.DEV) {
        console.log('fetchRecommendations called for user.id:', user.id, 'forceRegenerate:', forceRegenerate)
      }
      setLoading(true)
<<<<<<< Updated upstream
      if (user.id) {
        const data = await recommendationsService.get(user.id)
        setRecommendations(data)
=======
      setError(null)
      if (!user || !user.id) {
        console.error('User sau user.id lipsește!', user)
        setError('ID-ul utilizatorului lipsește. Vă rugăm să vă conectați din nou.')
        setLoading(false)
        return
      }
      
      const data = await recommendationsService.get(user.id, forceRegenerate)
      if (import.meta.env.DEV) {
        console.log('Recomandări primite:', data)
      }
      
      if (Array.isArray(data) && data.length > 0) {
        setRecommendations(data)
        setError(null)
      } else {
        if (import.meta.env.DEV) {
          console.log('Nu s-au găsit recomandări sau array-ul este gol')
        }
        setError('Nu s-au găsit recomandări. Vă rugăm să verificați profilul și analizele medicale.')
        setRecommendations([])
>>>>>>> Stashed changes
      }
    } catch (err) {
      console.error('Eroare la obținerea recomandărilor:', err)
<<<<<<< Updated upstream
      setError('Nu s-au putut genera recomandări. Vă rugăm să încercați din nou.')
=======
      // Extrage mesajul de eroare - axios interceptor-ul ar trebui să-l extragă deja
      let errorMessage = 'Nu s-au putut genera recomandări. Vă rugăm să încercați din nou.'
      
      if (err?.message) {
        errorMessage = err.message
      } else if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
        } else if (typeof detail === 'object') {
          errorMessage = detail.msg || detail.message || JSON.stringify(detail)
        }
      }
      
      setError(errorMessage)
      setRecommendations([])
>>>>>>> Stashed changes
    } finally {
      setLoading(false)
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
    const marginLeft = 20
    const marginRight = 20
    const marginTop = 25
    const marginBottom = 25
    const contentWidth = pageWidth - marginLeft - marginRight
    
    // Helper function pentru adăugare text cu wrapping corect
    const addText = (text: string, x: number, y: number, options: {
      fontSize?: number
      fontStyle?: 'normal' | 'bold' | 'italic' | 'bolditalic'
      maxWidth?: number
      lineHeight?: number
      color?: [number, number, number]
      align?: 'left' | 'center' | 'right' | 'justify'
    } = {}) => {
      const {
        fontSize = 10,
        fontStyle = 'normal',
        maxWidth = contentWidth,
        lineHeight = fontSize * 1.4,
        color = [0, 0, 0],
        align = 'left'
      } = options
      
      doc.setFontSize(fontSize)
      doc.setFont('helvetica', fontStyle)
      doc.setTextColor(color[0], color[1], color[2])
      
      const lines = doc.splitTextToSize(text, maxWidth)
      
      // Calculează poziția Y pentru aliniere
      let startY = y
      if (align === 'center') {
        lines.forEach((line: string) => {
          const textWidth = doc.getTextWidth(line)
          doc.text(line, x + (maxWidth - textWidth) / 2, startY)
          startY += lineHeight
        })
      } else if (align === 'right') {
        lines.forEach((line: string) => {
          const textWidth = doc.getTextWidth(line)
          doc.text(line, x + maxWidth - textWidth, startY)
          startY += lineHeight
        })
      } else {
        // left sau justify
        lines.forEach((line: string) => {
          doc.text(line, x, startY)
          startY += lineHeight
        })
      }
      
      return startY
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
    
    // Header profesional cu fundal gradient
    doc.setFillColor(0, 150, 200)
    doc.rect(0, 0, pageWidth, 40, 'F')
    
    // Logo/Titlu principal
    doc.setFontSize(24)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(255, 255, 255)
    const titleWidth = doc.getTextWidth('VitaBalance')
    doc.text('VitaBalance', (pageWidth - titleWidth) / 2, 20)
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    const subtitle = 'Raport de Recomandări Nutriționale Personalizate'
    const subtitleWidth = doc.getTextWidth(subtitle)
    doc.text(subtitle, (pageWidth - subtitleWidth) / 2, 30)
    
    y = marginTop + 50
    
    // Informații utilizator în casetă
    doc.setFillColor(240, 248, 255)
    doc.roundedRect(marginLeft, y, contentWidth, 20, 3, 3, 'F')
    
    doc.setFontSize(11)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 0, 0)
    doc.text('Beneficiar:', marginLeft + 3, y + 7)
    
    doc.setFont('helvetica', 'normal')
    doc.text(user.name || 'Utilizator', marginLeft + 25, y + 7)
    
    const dateText = `Data generării: ${new Date().toLocaleDateString('ro-RO', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })}`
    doc.text(dateText, marginLeft + 3, y + 14)
    
    y += 28
    
    // Disclaimer profesional
    checkNewPage(20)
    doc.setFillColor(255, 248, 220)
    doc.roundedRect(marginLeft, y, contentWidth, 15, 3, 3, 'F')
    
    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(200, 100, 0)
    doc.text('IMPORTANT:', marginLeft + 3, y + 6)
    
    doc.setFont('helvetica', 'normal')
    const disclaimerText = 'Aceste recomandări sunt sugestii generale bazate pe informațiile furnizate și nu înlocuiesc consultul medical profesional. Vă rugăm să consultați întotdeauna un medic sau nutriționist autorizat înainte de a face modificări majore în dieta dumneavoastră.'
    const disclaimerLines = doc.splitTextToSize(disclaimerText, contentWidth - 6)
    doc.setTextColor(100, 60, 0)
    disclaimerLines.forEach((line: string, idx: number) => {
      doc.text(line, marginLeft + 3, y + 10 + (idx * 4))
    })
    
    y += 20
    
    // Titlu secțiune recomandări
    checkNewPage(15)
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 100, 150)
    doc.text('RECOMANDĂRI NUTRIȚIONALE', marginLeft, y)
    
    y += 8
    doc.setDrawColor(0, 150, 200)
    doc.setLineWidth(0.5)
    doc.line(marginLeft, y, pageWidth - marginRight, y)
    y += 6
    
    // Recomandări
    recommendations.forEach((rec, index) => {
      checkNewPage(40)
      
      // Număr recomandare
      doc.setFillColor(0, 150, 200)
      doc.circle(marginLeft + 5, y + 4, 4, 'F')
      doc.setFontSize(10)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(255, 255, 255)
      doc.text((index + 1).toString(), marginLeft + 5, y + 6, { align: 'center' })
      
      // Titlu aliment
      doc.setFontSize(14)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(0, 100, 150)
      const foodNameLines = doc.splitTextToSize(rec.food.name, contentWidth - 20)
      foodNameLines.forEach((line: string, idx: number) => {
        doc.text(line, marginLeft + 12, y + (idx * 6) + 6)
      })
      y += foodNameLines.length * 6 + 4
      
      // Informații de bază în tabel format
      doc.setFontSize(10)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(60, 60, 60)
      
      const infoY = y
      doc.text('Categorie:', marginLeft + 12, infoY)
      doc.setFont('helvetica', 'bold')
      doc.text(rec.food.category, marginLeft + 35, infoY)
      
      doc.setFont('helvetica', 'normal')
      doc.text('Porție sugerată:', marginLeft + 12, infoY + 5)
      doc.setFont('helvetica', 'bold')
      doc.text(`${rec.explanation.portion}g`, marginLeft + 50, infoY + 5)
      
      doc.setFont('helvetica', 'normal')
      doc.text('Acoperire deficit:', marginLeft + 12, infoY + 10)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(0, 150, 0)
      doc.text(`${rec.coverage.toFixed(1)}%`, marginLeft + 50, infoY + 10)
      
      y = infoY + 16
      
      // Explicație principală
      checkNewPage(25)
      doc.setFontSize(10)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(0, 0, 0)
      doc.text('Descriere:', marginLeft + 12, y)
      y += 5
      
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(40, 40, 40)
      const explanationLines = doc.splitTextToSize(rec.explanation.text, contentWidth - 12)
      explanationLines.forEach((line: string) => {
        doc.text(line, marginLeft + 12, y)
        y += 4.5
      })
      
      y += 3
      
      // Motive
      checkNewPage(20)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(0, 0, 0)
      doc.text('Motivație recomandare:', marginLeft + 12, y)
      y += 5
      
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(40, 40, 40)
      rec.explanation.reasons.forEach(reason => {
        checkNewPage(8)
        const reasonLines = doc.splitTextToSize(`• ${reason}`, contentWidth - 15)
        reasonLines.forEach((line: string) => {
          doc.text(line, marginLeft + 15, y)
          y += 4.5
        })
      })
      
      // Sfaturi
      if (rec.explanation.tips && rec.explanation.tips.length > 0) {
        y += 3
        checkNewPage(20)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(0, 0, 0)
        doc.text('Sfaturi de preparare:', marginLeft + 12, y)
        y += 5
        
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(40, 40, 40)
        rec.explanation.tips.forEach(tip => {
          checkNewPage(8)
          const tipLines = doc.splitTextToSize(`• ${tip}`, contentWidth - 15)
          tipLines.forEach((line: string) => {
            doc.text(line, marginLeft + 15, y)
            y += 4.5
          })
        })
      }
      
      // Alternative
      if (rec.explanation.alternatives && rec.explanation.alternatives.length > 0) {
        y += 3
        checkNewPage(15)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(0, 0, 0)
        doc.text('Alternative recomandate:', marginLeft + 12, y)
        y += 5
        
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(40, 40, 40)
        const alternativesText = rec.explanation.alternatives.join(', ')
        const altLines = doc.splitTextToSize(alternativesText, contentWidth - 12)
        altLines.forEach((line: string) => {
          doc.text(line, marginLeft + 12, y)
          y += 4.5
        })
      }
      
      // Linie separator elegantă
      y += 8
      if (y > pageHeight - marginBottom - 5) {
        doc.addPage()
        y = marginTop
      }
      doc.setDrawColor(200, 200, 200)
      doc.setLineWidth(0.3)
      doc.line(marginLeft, y, pageWidth - marginRight, y)
      y += 10
    })
    
    // Footer profesional pe fiecare pagină
    const totalPages = doc.internal.pages.length - 1
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      
      // Linie footer
      doc.setDrawColor(200, 200, 200)
      doc.setLineWidth(0.3)
      doc.line(marginLeft, pageHeight - 15, pageWidth - marginRight, pageHeight - 15)
      
      // Text footer
      doc.setFontSize(8)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(120, 120, 120)
      
      const footerText = `VitaBalance - Pagina ${i} din ${totalPages}`
      const footerWidth = doc.getTextWidth(footerText)
      doc.text(footerText, (pageWidth - footerWidth) / 2, pageHeight - 10)
      
      // Copyright
      const copyrightText = `© ${new Date().getFullYear()} VitaBalance. Toate drepturile rezervate.`
      const copyrightWidth = doc.getTextWidth(copyrightText)
      doc.text(copyrightText, (pageWidth - copyrightWidth) / 2, pageHeight - 6)
    }
    
    // Nume fișier
    const safeName = (user.name || 'Utilizator').replace(/[^a-zA-Z0-9]/g, '_')
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

  if (error && !loading) {
    return (
      <GlassCard className="max-w-2xl mx-auto">
        <div className="text-center text-red-400">
          <p className="mb-4">{error}</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <motion.button 
              onClick={() => fetchRecommendations(true)} 
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

  // Error boundary - dacă nu există user
  if (!user) {
    return (
      <div className="w-full text-center py-12">
        <p className="text-red-400">Eroare: Date utilizator lipsă</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Date profil utilizator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <UserProfileInfo user={user} />
      </motion.div>

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
          />
        ))}
      </div>

      {loading && (
        <GlassCard className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neonCyan mb-4"></div>
          <p className="text-slate-300 text-lg">
            Se încarcă recomandările...
          </p>
        </GlassCard>
      )}

      {!loading && error && (
        <GlassCard className="text-center py-12">
          <p className="text-red-400 text-lg mb-4">
            {error}
          </p>
          <button
            onClick={() => fetchRecommendations(true)}
            className="px-4 py-2 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition"
          >
            Încearcă din nou
          </button>
        </GlassCard>
      )}

      {!loading && !error && recommendations.length === 0 && (
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

