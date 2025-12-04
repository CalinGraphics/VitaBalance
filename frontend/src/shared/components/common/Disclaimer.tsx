import { AlertTriangle, X } from 'lucide-react'
import { useState } from 'react'

const Disclaimer = () => {
  const [isVisible, setIsVisible] = useState(true)

  if (!isVisible) return null

  return (
    <div className="w-full mb-6">
      <div className="w-full rounded-2xl bg-yellow-900/40 border border-yellow-500/35 shadow-[0_18px_60px_rgba(0,0,0,0.55)] backdrop-blur-sm">
        <div className="px-5 py-3.5 flex items-start gap-3">
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

