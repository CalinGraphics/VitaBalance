import { useEffect, ReactNode } from 'react';

// Simplificat - doar dark mode, fără toggle
export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.add('dark');
  }, []);

  return <>{children}</>;
};

