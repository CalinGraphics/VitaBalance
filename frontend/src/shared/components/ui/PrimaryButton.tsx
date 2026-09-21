import React, { ReactNode } from 'react';

interface PrimaryButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  full?: boolean;
  disabled?: boolean;
  /** `primary` = accent solid; `secondary` = contur discret pentru acțiuni secundare; `danger` = acțiuni distructive. */
  variant?: 'primary' | 'secondary' | 'danger';
}

const VARIANTS = {
  primary: 'bg-accent text-accent-fg hover:bg-accent-hover active:bg-accent-strong',
  secondary: 'border border-line-strong bg-transparent text-zinc-100 hover:bg-white/5 active:bg-white/10',
  danger: 'border border-red-500/30 bg-transparent text-red-300 hover:bg-red-500/10 active:bg-red-500/15',
} as const;

const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  onClick,
  type = 'button',
  full = true,
  disabled = false,
  variant = 'primary',
}) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`inline-flex min-h-[44px] min-w-[44px] cursor-pointer items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold leading-5 transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 focus-visible:ring-offset-2 focus-visible:ring-offset-canvas disabled:cursor-not-allowed disabled:opacity-50 touch-manipulation ${VARIANTS[variant]} ${
      full ? 'w-full' : ''
    }`}
  >
    {children}
  </button>
);

export default PrimaryButton;
