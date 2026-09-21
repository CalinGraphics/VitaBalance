import React, { useEffect, useId, useRef, useState } from 'react'
import { Check, ChevronDown, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export interface MultiSelectOption {
  value: string
  label: string
  description?: string
}

interface MultiSelectFieldProps {
  label: string
  /** Valorile selectate. */
  selected: string[]
  options: MultiSelectOption[]
  onChange: (next: string[]) => void
  placeholder: string
  /** Text afișat pe buton când există selecții. */
  summary: (count: number) => string
  hint?: string
  /** Eticheta unei valori selectate care nu se află în `options` (valoare veche/necunoscută). */
  fallbackLabel?: (value: string) => string
}

/** Listă derulantă cu selecție multiplă, chip-uri pentru valorile alese; Esc și click în afară o închid. */
const MultiSelectField: React.FC<MultiSelectFieldProps> = ({
  label,
  selected,
  options,
  onChange,
  placeholder,
  summary,
  hint,
  fallbackLabel,
}) => {
  const { t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const id = useId()

  useEffect(() => {
    if (!isOpen) return
    const onPointerDown = (ev: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(ev.target as Node)) setIsOpen(false)
    }
    const onKeyDown = (ev: KeyboardEvent) => {
      if (ev.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [isOpen])

  const labelOf = (value: string): string =>
    options.find((o) => o.value === value)?.label ?? fallbackLabel?.(value) ?? value

  const toggle = (value: string) => {
    onChange(selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value])
  }

  return (
    <div className="mb-4">
      <label id={`${id}-label`} className="field-label">
        {label}
      </label>

      {selected.length > 0 && (
        <ul className="mb-2 flex flex-wrap gap-2">
          {selected.map((value) => (
            <li
              key={value}
              className="flex items-center gap-1 rounded-md border border-accent-border bg-accent-soft py-1 pl-2.5 pr-1 text-sm text-accent"
            >
              <span>{labelOf(value)}</span>
              <button
                type="button"
                onClick={() => toggle(value)}
                aria-label={t('selectors.remove', { item: labelOf(value) })}
                className="flex h-6 w-6 cursor-pointer items-center justify-center rounded transition-colors hover:bg-white/10 hover:text-red-400"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <div ref={containerRef} className="relative">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-labelledby={`${id}-label`}
          className="field flex cursor-pointer items-center justify-between gap-2 pr-3 text-left"
        >
          <span className={`truncate ${selected.length === 0 ? 'text-zinc-500' : 'text-zinc-200'}`}>
            {selected.length === 0 ? placeholder : summary(selected.length)}
          </span>
          <ChevronDown
            aria-hidden="true"
            className={`h-4 w-4 flex-shrink-0 text-zinc-400 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {isOpen && (
          <div
            role="listbox"
            aria-multiselectable="true"
            aria-labelledby={`${id}-label`}
            className="absolute z-30 mt-1.5 max-h-64 w-full overflow-y-auto rounded-lg border border-line-strong bg-surface p-1 shadow-pop animate-scale-in"
          >
            {options.map((option) => {
              const isSelected = selected.includes(option.value)
              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => toggle(option.value)}
                  className={`flex w-full cursor-pointer items-center justify-between gap-3 rounded-md px-3 py-2.5 text-left transition-colors ${
                    isSelected ? 'bg-accent-soft text-accent' : 'text-zinc-200 hover:bg-white/5'
                  }`}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium">{option.label}</span>
                    {option.description && (
                      <span className="mt-0.5 block text-xs text-zinc-500">{option.description}</span>
                    )}
                  </span>
                  {isSelected && <Check className="h-4 w-4 flex-shrink-0" aria-hidden="true" />}
                </button>
              )
            })}
          </div>
        )}
      </div>

      {hint && <p className="mt-1.5 text-xs text-zinc-500">{hint}</p>}
    </div>
  )
}

export default MultiSelectField
