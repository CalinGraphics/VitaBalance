import React, { useEffect, useMemo, useRef, useState } from 'react';

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

  const selectedLabel = useMemo(
    () => options.find((o) => o.value === value)?.label ?? '',
    [options, value]
  );

  useEffect(() => {
    const onPointerDown = (ev: MouseEvent) => {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(ev.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', onPointerDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
    };
  }, []);

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
      <label className="mb-1.5 block text-xs font-medium uppercase tracking-[0.16em] text-slate-300">
        {label}
      </label>

      <div ref={containerRef} className="relative">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="w-full min-h-[44px] rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2.5 pr-10 text-left text-sm text-slate-100 outline-none transition-all duration-200 focus:border-neonCyan/80 focus:ring-2 focus:ring-neonCyan/30 hover:border-neonPurple/50"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <span className="block truncate">{selectedLabel}</span>
        </button>

        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
          <svg
            className={`h-4 w-4 text-neonCyan transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>

        {isOpen && (
          <div
            role="listbox"
            className="absolute z-40 mt-2 w-full overflow-hidden rounded-xl border border-neonCyan/40 bg-slate-900/95 shadow-[0_0_22px_rgba(0,245,255,0.22)] backdrop-blur-sm"
          >
            {options.map((option) => {
              const active = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleOptionSelect(option.value)}
                  className={`block w-full px-3 py-2.5 text-left text-sm transition ${
                    active
                      ? 'bg-neonCyan/25 text-slate-50'
                      : 'text-slate-200 hover:bg-neonPurple/20 hover:text-slate-50'
                  }`}
                >
                  {option.label}
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

