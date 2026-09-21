import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface PageHeaderProps {
  Icon: LucideIcon;
  title: string;
  subtitle?: string;
  className?: string;
}

/** Antet de pagină: iconiță într-un tile discret + titlu + subtitlu. */
const PageHeader: React.FC<PageHeaderProps> = ({ Icon, title, subtitle, className = 'mb-6' }) => (
  <div className={`flex items-center gap-3.5 ${className}`}>
    <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg border border-accent-border bg-accent-soft text-accent">
      <Icon aria-hidden="true" className="h-5 w-5" />
    </div>
    <div className="min-w-0">
      <h1 className="text-xl font-semibold tracking-tight text-zinc-50 sm:text-2xl">{title}</h1>
      {subtitle && <p className="mt-0.5 text-sm text-zinc-400">{subtitle}</p>}
    </div>
  </div>
);

export default PageHeader;
