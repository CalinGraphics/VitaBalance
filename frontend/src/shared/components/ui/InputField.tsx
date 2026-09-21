import React, { useId, useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface InputFieldProps {
  label: string;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  placeholder?: string;
  error?: string;
  /** Text de ajutor afișat sub câmp (ascuns când există o eroare). */
  hint?: string;
  textarea?: boolean;
  rows?: number;
  step?: string;
  min?: string;
  max?: string;
  inputMode?: React.InputHTMLAttributes<HTMLInputElement>['inputMode'];
  pattern?: string;
  autoComplete?: string;
  required?: boolean;
  /** Când true și value e gol, câmpul arată mai estompat (pentru câmpuri opționale) */
  transparentWhenEmpty?: boolean;
}

const InputField: React.FC<InputFieldProps> = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  error,
  hint,
  textarea = false,
  rows = 3,
  step,
  min,
  max,
  inputMode,
  pattern,
  autoComplete,
  required = false,
  transparentWhenEmpty = false,
}) => {
  const id = useId();
  const { t } = useTranslation();
  const [revealed, setRevealed] = useState(false);
  const isPassword = type === 'password';
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  const isEmpty = !value || value.trim() === '';
  const ghost = transparentWhenEmpty && isEmpty ? 'opacity-80' : '';
  const className = `field ${error ? 'field-error' : ''} ${ghost}`;

  return (
    <div className="mb-4">
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      {textarea ? (
        <textarea
          id={id}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          rows={rows}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`${className} min-h-[88px]`}
        />
      ) : (
        <div className="relative">
          <input
            id={id}
            type={isPassword && revealed ? 'text' : type}
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            step={step}
            min={min}
            max={max}
            inputMode={inputMode}
            pattern={pattern}
            required={required}
            aria-invalid={error ? true : undefined}
            aria-describedby={describedBy}
            className={`${className} ${isPassword ? 'pr-11' : ''}`}
            autoComplete={autoComplete ?? (isPassword ? 'current-password' : 'off')}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setRevealed((prev) => !prev)}
              aria-label={revealed ? t('common.hidePassword') : t('common.showPassword')}
              aria-pressed={revealed}
              className="absolute inset-y-0 right-0 flex w-11 cursor-pointer items-center justify-center rounded-r-lg text-zinc-500 transition-colors hover:text-zinc-200 touch-manipulation"
            >
              {revealed ? <EyeOff aria-hidden="true" className="h-4 w-4" /> : <Eye aria-hidden="true" className="h-4 w-4" />}
            </button>
          )}
        </div>
      )}
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-zinc-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
};

export default InputField;
