/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        // Accent unic de brand (teal, identitate de nutriție/sănătate) — singura culoare "vie" din UI.
        accent: {
          DEFAULT: '#2dd4bf',
          hover: '#5eead4',
          strong: '#14b8a6',
          fg: '#04201c', // text pe fundal accent (contrast > 10:1)
          soft: 'rgba(45, 212, 191, 0.10)',
          border: 'rgba(45, 212, 191, 0.32)',
        },
        // Scara teal păstrată pentru grafice și stări secundare
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        // Fundal și suprafețe aproape monocrome (neutre, fără dominantă albastră)
        canvas: '#08090a',
        surface: '#101113',
        'surface-hover': '#17181b',
        line: 'rgba(255, 255, 255, 0.08)',
        'line-strong': 'rgba(255, 255, 255, 0.16)',
      },
      borderRadius: {
        card: '14px',
      },
      boxShadow: {
        // Umbră discretă, fără glow colorat
        card: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 12px 32px -16px rgba(0,0,0,0.7)',
        pop: '0 12px 32px -8px rgba(0,0,0,0.75)',
      },
      transitionDuration: {
        DEFAULT: '180ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.18s ease-out',
        aurora: 'aurora 18s ease-in-out infinite alternate',
        'aurora-slow': 'aurora 26s ease-in-out infinite alternate-reverse',
        'ping-slow': 'pingSlow 2.8s cubic-bezier(0, 0, 0.2, 1) infinite',
        shimmer: 'shimmer 6s linear infinite',
        'grow-x': 'growX 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        float: 'float 7s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        aurora: {
          '0%': { transform: 'translate3d(0, 0, 0) scale(1)' },
          '50%': { transform: 'translate3d(40px, 24px, 0) scale(1.12)' },
          '100%': { transform: 'translate3d(-24px, 40px, 0) scale(0.95)' },
        },
        growX: {
          '0%': { transform: 'scaleX(0)', opacity: '0' },
          '100%': { transform: 'scaleX(1)', opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        pingSlow: {
          '0%': { transform: 'scale(1)', opacity: '0.6' },
          '70%, 100%': { transform: 'scale(1.35)', opacity: '0' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.97)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
