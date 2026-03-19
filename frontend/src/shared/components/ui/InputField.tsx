import React from 'react';

interface InputFieldProps {
  label: string;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  placeholder?: string;
  error?: string;
  textarea?: boolean;
  rows?: number;
  step?: string;
  inputMode?: React.InputHTMLAttributes<HTMLInputElement>['inputMode'];
  pattern?: string;
  /** Când true și value e gol, câmpul arată mai transparent (pentru câmpuri opționale) */
  transparentWhenEmpty?: boolean;
}

const InputField: React.FC<InputFieldProps> = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  textarea = false,
  rows = 3,
  step,
  inputMode,
  pattern,
  transparentWhenEmpty = false,
}) => {
  const isEmpty = !value || value.trim() === '';
  const useGhostStyle = transparentWhenEmpty && isEmpty;
  // Base classes - când gol și transparentWhenEmpty: fundal mai transparent, placeholder mai subtil
  const baseClasses = useGhostStyle
    ? 'w-full min-h-[44px] rounded-xl px-3 py-3 sm:py-2.5 text-base sm:text-sm text-slate-100 placeholder:text-slate-500/60 transition-all bg-slate-950/20'
    : 'w-full min-h-[44px] rounded-xl px-3 py-3 sm:py-2.5 text-base sm:text-sm text-slate-100 placeholder:text-slate-500 transition-all bg-slate-950/40';
  
  const borderClass = error 
    ? 'focus:ring-red-500/30 focus:ring-2' 
    : 'focus:ring-neonCyan/30 focus:ring-2';

  // Force styles with inline styles to override everything
  const inputStyle: React.CSSProperties = {
    WebkitAppearance: 'none',
    MozAppearance: 'none',
    appearance: 'none',
    boxShadow: 'none',
    WebkitBoxShadow: 'none',
    MozBoxShadow: 'none',
    outline: 'none',
    outlineOffset: '0',
    outlineWidth: '0',
    outlineStyle: 'none',
    border: error 
      ? '1px solid rgba(239, 68, 68, 0.8)' 
      : useGhostStyle 
        ? '1px solid rgba(255, 255, 255, 0.06)' 
        : '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '0.75rem',
    backgroundColor: useGhostStyle ? 'rgba(2, 6, 23, 0.15)' : 'rgba(2, 6, 23, 0.4)',
    color: 'rgb(241, 245, 249)',
  };

  const focusStyle: React.CSSProperties = {
    ...inputStyle,
    border: error
      ? '1px solid rgba(239, 68, 68, 1)'
      : '1px solid rgba(0, 245, 255, 0.8)',
    boxShadow: error
      ? '0 0 0 2px rgba(239, 68, 68, 0.3)'
      : '0 0 0 2px rgba(0, 245, 255, 0.3)',
  };

  return (
    <div className="mb-4">
      <label className="mb-1.5 block text-xs font-medium uppercase tracking-[0.16em] text-slate-300">
        {label}
      </label>
      {textarea ? (
        <textarea
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          rows={rows}
          className={`${baseClasses} min-h-[88px] ${borderClass}`}
          style={inputStyle}
          onFocus={(e) => {
            Object.assign(e.target.style, focusStyle);
          }}
          onBlur={(e) => {
            Object.assign(e.target.style, inputStyle);
          }}
        />
      ) : (
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          step={step}
          inputMode={inputMode}
          pattern={pattern}
          className={`${baseClasses} ${borderClass}`}
          style={inputStyle}
          onFocus={(e) => {
            Object.assign(e.target.style, focusStyle);
          }}
          onBlur={(e) => {
            Object.assign(e.target.style, inputStyle);
          }}
          autoComplete={type === 'password' ? 'current-password' : 'off'}
        />
      )}
      {error && (
        <p className="mt-1 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
};

export default InputField;
