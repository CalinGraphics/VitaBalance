import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ChevronDown, X } from 'lucide-react'
import {
  COMMON_MEDICAL_CONDITIONS,
  parseMedicalConditions,
  stringifyMedicalConditions,
} from '../../constants/medicalConditions'

interface MedicalConditionSelectorProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

const MedicalConditionSelector = ({
  label,
  value,
  onChange,
  placeholder = 'Selectează condițiile medicale',
}: MedicalConditionSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const selected = parseMedicalConditions(value)

  const handleToggle = (conditionValue: string) => {
    const current = parseMedicalConditions(value)
    const isSelected = current.includes(conditionValue)
    if (isSelected) {
      onChange(stringifyMedicalConditions(current.filter(c => c !== conditionValue)))
    } else {
      onChange(stringifyMedicalConditions([...current, conditionValue]))
    }
  }

  const handleRemove = (conditionValue: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const current = parseMedicalConditions(value)
    onChange(stringifyMedicalConditions(current.filter(c => c !== conditionValue)))
  }

  const getSelectedLabel = (v: string): string => {
    return COMMON_MEDICAL_CONDITIONS.find(c => c.value === v)?.label || v
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selected.map((condition) => (
            <motion.div
              key={condition}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-1 px-3 py-1 bg-neonPurple/20 border border-neonPurple/50 rounded-lg text-sm text-neonPurple"
            >
              <span>{getSelectedLabel(condition)}</span>
              <button
                type="button"
                onClick={(e) => handleRemove(condition, e)}
                className="hover:text-red-400 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </motion.div>
          ))}
        </div>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-4 py-3 rounded-xl border border-white/20 bg-white/5 backdrop-blur-sm text-left text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-neonPurple focus:border-transparent transition-all hover:border-neonPurple/50 flex items-center justify-between"
        >
          <span className={selected.length === 0 ? 'text-slate-500' : 'text-slate-300'}>
            {selected.length === 0 ? placeholder : `${selected.length} condiții selectate`}
          </span>
          <ChevronDown
            className={`w-5 h-5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        <AnimatePresence>
          {isOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute z-20 w-full mt-2 rounded-xl border border-white/20 bg-slate-900/95 backdrop-blur-lg shadow-xl max-h-64 overflow-y-auto"
              >
                <div className="p-2">
                  {COMMON_MEDICAL_CONDITIONS.map((condition) => {
                    const isSelected = selected.includes(condition.value)
                    return (
                      <button
                        key={condition.value}
                        type="button"
                        onClick={() => handleToggle(condition.value)}
                        className={`w-full px-4 py-3 rounded-lg text-left transition-all flex items-center justify-between ${
                          isSelected
                            ? 'bg-neonPurple/20 text-neonPurple border border-neonPurple/50'
                            : 'text-slate-300 hover:bg-white/10 border border-transparent'
                        }`}
                      >
                        <div className="flex-1">
                          <div className="font-medium">{condition.label}</div>
                          {condition.description && (
                            <div className="text-xs text-slate-400 mt-1">{condition.description}</div>
                          )}
                        </div>
                        {isSelected && (
                          <Check className="w-5 h-5 text-neonPurple flex-shrink-0 ml-2" />
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
        Selectează condițiile care te afectează. Recomandările vor ține cont de acestea.
      </p>
    </div>
  )
}

export default MedicalConditionSelector
