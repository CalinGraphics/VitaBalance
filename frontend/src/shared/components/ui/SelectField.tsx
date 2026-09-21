import React, { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  options: { value: string; label: string }[];
  className?: string;
}

const SelectField: React.FC<SelectFieldProps> = ({
  label,
  value,
  onChange,
  options,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const id = useId();

  const selectedLabel = useMemo(
    () => options.find((o) => o.value === value)?.label ?? '',
    [options, value]
  );

  useEffect(() => {
    if (!isOpen) return;
    const onPointerDown = (ev: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(ev.target as Node)) {
        setIsOpen(false);
      }
    };
    const onKeyDown = (ev: KeyboardEvent) => {
      if (ev.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [isOpen]);

  const handleOptionSelect = (nextValue: string) => {
    setIsOpen(false);
    const syntheticEvent = {
      target: { value: nextValue },
      currentTarget: { value: nextValue },
    } as React.ChangeEvent<HTMLSelectElement>;
    onChange(syntheticEvent);
  };

  return (
    <div className={`mb-4 ${className}`}>
      <label id={`${id}-label`} className="field-label">
        {label}
      </label>

      <div ref={containerRef} className="relative">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="field flex cursor-pointer items-center justify-between gap-2 pr-3 text-left"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-labelledby={`${id}-label`}
        >
          <span className="block truncate">{selectedLabel}</span>
          <ChevronDown
            aria-hidden="true"
            className={`h-4 w-4 flex-shrink-0 text-zinc-400 transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {isOpen && (
          <div
            role="listbox"
            aria-labelledby={`${id}-label`}
            className="absolute z-40 mt-1.5 w-full overflow-hidden rounded-lg border border-line-strong bg-surface p-1 shadow-pop animate-scale-in"
          >
            {options.map((option) => {
              const active = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={active}
                  onClick={() => handleOptionSelect(option.value)}
                  className={`flex w-full cursor-pointer items-center justify-between gap-2 rounded-md px-3 py-2.5 text-left text-sm transition-colors ${
                    active
                      ? 'bg-accent-soft text-accent'
                      : 'text-zinc-200 hover:bg-white/5 hover:text-zinc-50'
                  }`}
                >
                  <span className="truncate">{option.label}</span>
                  {active && <Check aria-hidden="true" className="h-4 w-4 flex-shrink-0" />}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SelectField;
