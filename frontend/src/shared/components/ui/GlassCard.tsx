import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
}

const GlassCard: React.FC<GlassCardProps> = ({ children, className = '' }) => (
  <motion.div
    initial={{ opacity: 0, y: 32, scale: 0.97 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    transition={{ duration: 0.5, ease: 'easeOut' }}
    className={`relative w-full max-w-full rounded-2xl md:rounded-3xl border border-white/10 bg-slate-900/40 backdrop-blur-xl shadow-[0_0_60px_rgba(15,23,42,0.6)] overflow-hidden ${className}`}
  >
    {/* Border glow effect */}
    <div className="pointer-events-none absolute inset-px rounded-[14px] md:rounded-[22px] bg-gradient-to-br from-white/15 via-transparent to-neonMagenta/40 opacity-70" />
    {/* Content */}
    <div className="relative p-5 sm:p-6 md:p-8">{children}</div>
  </motion.div>
);

export default GlassCard;

