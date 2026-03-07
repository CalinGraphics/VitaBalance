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
      boxShadow: '0 0 40px rgba(34,211,238,0.6), 0 0 55px rgba(37,99,235,0.6)' 
    }}
    whileTap={disabled ? {} : { scale: 0.98 }}
    type={type}
    onClick={onClick}
    disabled={disabled}
    className={`group relative inline-flex items-center justify-center overflow-hidden min-h-[44px] min-w-[44px] rounded-xl px-6 py-3.5 text-sm font-semibold text-white bg-gradient-to-r from-cyan-400 via-sky-500 to-blue-600 shadow-[0_0_25px_rgba(34,211,238,0.5)] transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/80 disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation ${
      full ? 'w-full' : ''
    }`}
  >
    {/* Animated gradient overlay */}
    <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -translate-x-full opacity-60 group-hover:translate-x-full transition-transform duration-700" />
    
    {/* Content */}
    <span className="relative z-10 flex items-center gap-2 leading-5">
      {children}
    </span>
    
    {/* Shimmer effect */}
    <motion.div
      className="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
      initial={{ x: '-120%' }}
      animate={disabled ? {} : {
        x: ['-120%', '220%'],
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

