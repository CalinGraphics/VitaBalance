import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

const Disclaimer = () => {
  const [isVisible, setIsVisible] = useState(true)

  if (!isVisible) return null

  return (
    <div className="bg-yellow-900/30 border-b border-yellow-500/30 sticky top-0 z-50 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-yellow-200 font-medium">
              <strong>Disclaimer medical:</strong> Această aplicație oferă sugestii generale și nu înlocuiește 
              consultul medical. Pentru probleme de sănătate, vă rugăm să consultați un specialist. 
              Recomandările sunt bazate pe informații generale și pot să nu fie potrivite pentru toți utilizatorii.
            </p>
          </div>
          <button
            onClick={() => setIsVisible(false)}
            className="text-yellow-400 hover:text-yellow-200 transition-colors"
            aria-label="Închide"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default Disclaimer

