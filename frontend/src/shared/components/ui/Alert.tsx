import React, { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

type AlertVariant = 'error' | 'success' | 'info' | 'warning';

interface AlertProps {
  variant?: AlertVariant;
  children: ReactNode;
  className?: string;
}

const STYLES: Record<AlertVariant, { box: string; Icon: typeof Info }> = {
  error: { box: 'border-red-500/30 bg-red-500/[0.08] text-red-200', Icon: AlertCircle },
  success: { box: 'border-accent-border bg-accent-soft text-accent-hover', Icon: CheckCircle2 },
  info: { box: 'border-line-strong bg-white/[0.03] text-zinc-300', Icon: Info },
  warning: { box: 'border-amber-400/25 bg-amber-400/[0.06] text-amber-100', Icon: AlertCircle },
};

/** Mesaj inline de stare (eroare/succes/info). Erorile sunt anunțate imediat de cititoarele de ecran. */
const Alert: React.FC<AlertProps> = ({ variant = 'info', children, className = '' }) => {
  const { box, Icon } = STYLES[variant];
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm leading-relaxed ${box} ${className}`}
    >
      <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 flex-shrink-0" />
      <div className="min-w-0 flex-1 break-words">{children}</div>
    </div>
  );
};

export default Alert;
