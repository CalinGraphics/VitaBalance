import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  /** Padding intern; dezactivează-l pentru carduri cu conținut edge-to-edge. */
  padded?: boolean;
}

/**
 * Card de suprafață: fundal solid aproape negru, bordură fină de 1px, fără blur sau glow.
 * (Numele `GlassCard` e păstrat pentru compatibilitate cu importurile existente.)
 */
const GlassCard: React.FC<GlassCardProps> = ({ children, className = '', padded = true }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.25, ease: 'easeOut' }}
    className={`relative w-full max-w-full rounded-card border border-line bg-surface shadow-card ${className}`}
  >
    <div className={padded ? 'relative p-5 sm:p-6 md:p-8' : 'relative'}>{children}</div>
  </motion.div>
);

export default GlassCard;
