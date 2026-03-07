import React, { ReactNode, useState } from 'react';
import { Menu, X } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
  onLogout?: () => void;
  showLogout?: boolean;
  onProfileClick?: () => void;
  showProfile?: boolean;
  onLabResultsClick?: () => void;
  showLabResults?: boolean;
  onDashboardClick?: () => void;
  showDashboard?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, onLogout, showLogout, onProfileClick, showProfile, onLabResultsClick, showLabResults, onDashboardClick, showDashboard }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navButtons = (
    <>
      {showDashboard && onDashboardClick && (
        <button
          onClick={() => { onDashboardClick(); setMobileMenuOpen(false); }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-sm md:text-xs font-semibold text-slate-400 hover:text-neonCyan transition px-4 py-3 md:py-2 rounded-xl md:rounded-lg border border-white/10 hover:border-neonCyan/50 touch-manipulation"
        >
          Recomandări
        </button>
      )}
      {showLabResults && onLabResultsClick && (
        <button
          onClick={() => { onLabResultsClick(); setMobileMenuOpen(false); }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-sm md:text-xs font-semibold text-slate-400 hover:text-neonCyan transition px-4 py-3 md:py-2 rounded-xl md:rounded-lg border border-white/10 hover:border-neonCyan/50 touch-manipulation"
        >
          Analize medicale
        </button>
      )}
      {showProfile && onProfileClick && (
        <button
          onClick={() => { onProfileClick(); setMobileMenuOpen(false); }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-sm md:text-xs font-semibold text-slate-400 hover:text-neonCyan transition px-4 py-3 md:py-2 rounded-xl md:rounded-lg border border-white/10 hover:border-neonCyan/50 touch-manipulation"
        >
          Profil
        </button>
      )}
      {showLogout && onLogout && (
        <button
          onClick={() => { onLogout(); setMobileMenuOpen(false); }}
          className="min-h-[44px] min-w-[44px] flex items-center justify-center text-sm md:text-xs font-semibold text-slate-400 hover:text-neonMagenta transition px-4 py-3 md:py-2 rounded-xl md:rounded-lg border border-white/10 hover:border-neonMagenta/50 touch-manipulation"
        >
          Delogare
        </button>
      )}
    </>
  );

  return (
    <div className="min-h-screen app-gradient-dark text-slate-100 transition-colors duration-500 overflow-x-hidden">
      <div className="relative min-h-screen flex flex-col items-center justify-start px-3 py-4 sm:px-4 sm:py-6">
        {/* Glow background decorations */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -top-32 -left-24 h-72 w-72 rounded-full bg-neonCyan/30 blur-3xl" />
          <div className="absolute -bottom-32 -right-24 h-72 w-72 rounded-full bg-neonMagenta/30 blur-3xl" />
          <div className="absolute inset-0 bg-gradient-to-br from-transparent via-purple-500/10 to-transparent" />
        </div>

        {/* Navbar */}
        <header className="z-10 mb-6 md:mb-8 w-full max-w-7xl flex items-center justify-between">
          <div className="flex items-center min-w-0 flex-1">
            <img
              src="/logo.png"
              alt="VitaBalance Logo"
              className="h-20 w-auto object-contain object-left drop-shadow-lg sm:h-28 md:h-44 lg:h-56 xl:h-60"
            />
          </div>
          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-3">
            {navButtons}
          </div>
          {/* Mobile hamburger */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border border-white/10 hover:border-neonCyan/50 text-slate-300 hover:text-neonCyan transition touch-manipulation"
              aria-label={mobileMenuOpen ? 'Închide meniul' : 'Deschide meniul'}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </header>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden z-20 w-full max-w-7xl mb-4 rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl p-4 flex flex-col gap-2">
            {navButtons}
          </div>
        )}

        {/* Content */}
        <main className="z-10 w-full max-w-7xl flex-1 flex items-start justify-center py-3 sm:py-4 px-0 sm:px-0">
          {children}
        </main>

        <footer className="z-10 mt-6 md:mt-8 text-xs sm:text-xs text-slate-400 px-2">
          © {new Date().getFullYear()} VitaBalance
        </footer>
      </div>
    </div>
  );
};

export default Layout;

