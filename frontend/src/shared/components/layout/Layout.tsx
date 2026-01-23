import React, { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
  onLogout?: () => void;
  showLogout?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, onLogout, showLogout }) => {
  return (
    <div className="min-h-screen app-gradient-dark text-slate-100 transition-colors duration-500">
      <div className="relative min-h-screen flex flex-col items-center justify-start px-4 py-6">
        {/* Glow background decorations */}
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute -top-32 -left-24 h-72 w-72 rounded-full bg-neonCyan/30 blur-3xl" />
          <div className="absolute -bottom-32 -right-24 h-72 w-72 rounded-full bg-neonMagenta/30 blur-3xl" />
          <div className="absolute inset-0 bg-gradient-to-br from-transparent via-purple-500/10 to-transparent" />
        </div>

        {/* Navbar */}
        <header className="z-10 mb-8 w-full max-w-7xl flex items-center justify-between">
          <div className="flex items-center">
            <img 
              src="/logo.png" 
              alt="VitaBalance Logo" 
              className="h-40 w-auto object-contain drop-shadow-lg"
            />
          </div>
          {showLogout && onLogout && (
            <button
              onClick={onLogout}
              className="text-xs font-semibold text-slate-400 hover:text-neonMagenta transition px-4 py-2 rounded-lg border border-white/10 hover:border-neonMagenta/50"
            >
              Delogare
            </button>
          )}
        </header>

        {/* Content */}
        <main className="z-10 w-full max-w-7xl flex-1 flex items-start justify-center py-4">
          {children}
        </main>

        <footer className="z-10 mt-8 text-xs text-slate-400">
          © {new Date().getFullYear()} VitaBalance
        </footer>
      </div>
    </div>
  );
};

export default Layout;

