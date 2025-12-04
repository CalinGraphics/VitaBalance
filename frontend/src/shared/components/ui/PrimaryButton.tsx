import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface PrimaryButtonProps {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  full?: boolean;
  disabled?: boolean;
}

const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  onClick,
  type = 'button',
  full = true,
  disabled = false,
}) => (
  <motion.button
    whileHover={disabled ? {} : { 
      scale: 1.02, 
      boxShadow: '0 0 40px rgba(0,245,255,0.7), 0 0 60px rgba(168,85,255,0.5)' 
    }}
    whileTap={disabled ? {} : { scale: 0.98 }}
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`group relative inline-flex items-center justify-center overflow-hidden rounded-xl border-0 bg-gradient-to-r from-neonMagenta via-neonPurple to-neonCyan px-6 py-3.5 text-base font-bold text-slate-950 shadow-[0_0_25px_rgba(0,245,255,0.5)] transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neonCyan/50 disabled:opacity-50 disabled:cursor-not-allowed ${
      full ? 'w-full' : ''
    }`}
  >
    {/* Animated gradient overlay */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
    
    {/* Content */}
    <span className="relative z-10 flex items-center gap-2">{children}</span>
    
    {/* Shimmer effect */}
    <motion.div
      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
      initial={{ x: '-100%' }}
      animate={disabled ? {} : {
        x: ['-100%', '200%'],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        repeatDelay: 3,
        ease: 'easeInOut',
      }}
    />
  </motion.button>
);

export default PrimaryButton;

