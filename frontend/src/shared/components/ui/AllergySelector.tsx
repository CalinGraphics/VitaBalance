import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ChevronDown, X } from 'lucide-react'
import { COMMON_ALLERGIES, parseAllergies, stringifyAllergies, type AllergyOption } from '../../constants/allergies'

interface AllergySelectorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const AllergySelector = ({ label, value, onChange, placeholder = 'Selectează alergiile' }: AllergySelectorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const selectedAllergies = parseAllergies(value)
  
  const handleToggle = (allergyValue: string) => {
    const current = parseAllergies(value)
    const isSelected = current.includes(allergyValue)
    
    if (isSelected) {
      // Elimină alergia
      const updated = current.filter(a => a !== allergyValue)
      onChange(stringifyAllergies(updated))
    } else {
      // Adaugă alergia
      const updated = [...current, allergyValue]
      onChange(stringifyAllergies(updated))
    }
  }
  
  const handleRemove = (allergyValue: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const current = parseAllergies(value)
    const updated = current.filter(a => a !== allergyValue)
    onChange(stringifyAllergies(updated))
  }
  
  const getSelectedLabel = (value: string): string => {
    const allergy = COMMON_ALLERGIES.find(a => a.value === value)
    return allergy?.label || value
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300 mb-2">
        {label}
      </label>
      
      {/* Selected allergies display */}
      {selectedAllergies.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedAllergies.map((allergy) => (
            <motion.div
              key={allergy}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-1 px-3 py-1 bg-neonCyan/20 border border-neonCyan/50 rounded-lg text-sm text-neonCyan"
            >
              <span>{getSelectedLabel(allergy)}</span>
              <button
                type="button"
                onClick={(e) => handleRemove(allergy, e)}
                className="hover:text-red-400 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </motion.div>
          ))}
        </div>
      )}
      
      {/* Dropdown button */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-3 rounded-xl border border-white/20 bg-white/5 backdrop-blur-sm text-left text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-neonCyan focus:border-transparent transition-all hover:border-neonCyan/50 flex items-center justify-between"
        >
          <span className={selectedAllergies.length === 0 ? 'text-slate-500' : 'text-slate-300'}>
            {selectedAllergies.length === 0 ? placeholder : `${selectedAllergies.length} alergii selectate`}
          </span>
          <ChevronDown 
            className={`w-5 h-5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          />
        </button>
        
        {/* Dropdown menu */}
        <AnimatePresence>
          {isOpen && (
            <>
              <div 
                className="fixed inset-0 z-10" 
                onClick={() => setIsOpen(false)}
              />
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute z-20 w-full mt-2 rounded-xl border border-white/20 bg-slate-900/95 backdrop-blur-lg shadow-xl max-h-64 overflow-y-auto"
              >
                <div className="p-2">
                  {COMMON_ALLERGIES.map((allergy) => {
                    const isSelected = selectedAllergies.includes(allergy.value)
                    return (
                      <button
                        key={allergy.value}
                        type="button"
                        onClick={() => handleToggle(allergy.value)}
                        className={`w-full px-4 py-3 rounded-lg text-left transition-all flex items-center justify-between ${
                          isSelected
                            ? 'bg-neonCyan/20 text-neonCyan border border-neonCyan/50'
                            : 'text-slate-300 hover:bg-white/10 border border-transparent'
                        }`}
                      >
                        <div className="flex-1">
                          <div className="font-medium">{allergy.label}</div>
                          {allergy.description && (
                            <div className="text-xs text-slate-400 mt-1">{allergy.description}</div>
                          )}
                        </div>
                        {isSelected && (
                          <Check className="w-5 h-5 text-neonCyan flex-shrink-0 ml-2" />
                        )}
                      </button>
                    )
                  })}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>
      
      <p className="text-xs text-slate-500">
        Selectează toate alergiile care te afectează. Recomandările vor exclude automat alimentele care conțin aceste alergeni.
      </p>
    </div>
  )
}

export default AllergySelector
