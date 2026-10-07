import React, { ReactNode } from 'react';
import { Activity, FlaskConical, LayoutDashboard, LogOut, User, type LucideIcon } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { AuthUser, Route } from '../../types';
import Avatar from '../ui/Avatar';
import LanguageSwitcher from './LanguageSwitcher';

interface LayoutProps {
  children: ReactNode;
  /** Ruta curentă — folosită pentru starea activă din navigație. */
  route: Route;
  /** Navigația principală + logout apar doar pentru utilizatorul autentificat cu profil complet. */
  showNav?: boolean;
  onNavigate?: (route: Route) => void;
  onLogout?: () => void;
  /** Utilizatorul autentificat: numele și poza apar în antet. */
  user?: AuthUser | null;
}

interface NavItem {
  route: Route;
  labelKey: string;
  /** Eticheta scurtă din bara de jos (mobil), unde patru tab-uri împart lățimea ecranului. */
  shortLabelKey?: string;
  Icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { route: 'recommendations', labelKey: 'nav.dashboard', Icon: LayoutDashboard },
  { route: 'lab-results', labelKey: 'nav.labs', shortLabelKey: 'nav.labsShort', Icon: FlaskConical },
  { route: 'progress', labelKey: 'nav.progress', Icon: Activity },
  { route: 'edit-profile', labelKey: 'nav.profile', Icon: User },
];

const Layout: React.FC<LayoutProps> = ({ children, route, showNav = false, onNavigate, onLogout, user }) => {
  const { t } = useTranslation();
  const navigable = showNav && !!onNavigate;

  return (
    <div className="app-bg min-h-screen text-zinc-100 overflow-x-hidden flex flex-col">
      <header className="sticky top-0 z-30 border-b border-line bg-canvas/85 backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-3 px-4 md:h-16 md:gap-6">
          <img
            src="/logo-wordmark.png"
            alt={t('nav.logoAlt')}
            className="h-6 w-auto flex-shrink-0 object-contain object-left md:h-7"
          />

          {navigable && (
            <nav aria-label={t('nav.label')} className="hidden md:flex items-center gap-1 pl-2">
              {NAV_ITEMS.map(({ route: target, labelKey, Icon }) => {
                const active = route === target;
                return (
                  <button
                    key={target}
                    type="button"
                    onClick={() => onNavigate?.(target)}
                    aria-current={active ? 'page' : undefined}
                    className={`relative flex min-h-[40px] cursor-pointer items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors ${
                      active
                        ? 'bg-white/[0.07] text-zinc-50'
                        : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-100'
                    }`}
                  >
                    <Icon aria-hidden="true" className={`h-4 w-4 ${active ? 'text-accent' : ''}`} />
                    {t(labelKey)}
                    {active && (
                      <span
                        aria-hidden="true"
                        className="absolute -bottom-3 left-3 right-3 h-0.5 rounded-full bg-accent"
                      />
                    )}
                  </button>
                );
              })}
            </nav>
          )}

          <div className="ml-auto flex items-center gap-2">
            <LanguageSwitcher />
            {user &&
              (navigable ? (
                <button
                  type="button"
                  onClick={() => onNavigate?.('edit-profile')}
                  aria-label={t('nav.account', { name: user.fullName || user.email })}
                  title={user.fullName || user.email}
                  className="flex min-h-[40px] min-w-[40px] cursor-pointer items-center justify-center rounded-full transition-opacity hover:opacity-85 touch-manipulation"
                >
                  <Avatar name={user.fullName || user.email} url={user.avatarUrl} size={34} alt="" />
                </button>
              ) : (
                <Avatar
                  name={user.fullName || user.email}
                  url={user.avatarUrl}
                  size={34}
                  alt={t('nav.account', { name: user.fullName || user.email })}
                />
              ))}
            {navigable && onLogout && (
              <button
                type="button"
                onClick={onLogout}
                aria-label={t('nav.logout')}
                className="flex min-h-[40px] min-w-[40px] cursor-pointer items-center justify-center gap-2 rounded-lg border border-line px-2.5 text-sm font-medium text-zinc-400 transition-colors hover:border-line-strong hover:bg-white/5 hover:text-zinc-100 md:px-3 touch-manipulation"
              >
                <LogOut aria-hidden="true" className="h-4 w-4" />
                <span className="hidden md:inline">{t('nav.logout')}</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <main
        className={`mx-auto flex w-full max-w-7xl flex-1 items-start justify-center px-4 py-6 md:py-10 ${
          navigable ? 'pb-24 md:pb-10' : ''
        }`}
      >
        {children}
      </main>

      <footer className="px-4 pb-6 text-center text-xs text-zinc-500 md:pb-8">
        {t('nav.footer', { year: new Date().getFullYear() })}
      </footer>

      {/* Mobil: bară de tab-uri fixă jos — navigația e mereu la îndemână, fără meniu ascuns */}
      {navigable && (
        <nav
          aria-label={t('nav.label')}
          className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-canvas/95 backdrop-blur-md md:hidden"
          style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
        >
          <ul className="mx-auto grid max-w-md grid-cols-4">
            {NAV_ITEMS.map(({ route: target, labelKey, shortLabelKey, Icon }) => {
              const active = route === target;
              return (
                <li key={target}>
                  <button
                    type="button"
                    onClick={() => onNavigate?.(target)}
                    aria-current={active ? 'page' : undefined}
                    aria-label={t(labelKey)}
                    className={`flex min-h-[56px] w-full cursor-pointer flex-col items-center justify-center gap-1 text-[11px] font-medium transition-colors touch-manipulation ${
                      active ? 'text-accent' : 'text-zinc-400 active:text-zinc-100'
                    }`}
                  >
                    <Icon aria-hidden="true" className="h-5 w-5" />
                    <span className="max-w-full truncate px-1">{t(shortLabelKey ?? labelKey)}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>
      )}
    </div>
  );
};

export default Layout;
