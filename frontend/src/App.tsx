import { useTranslation } from 'react-i18next'
import { ThemeProvider } from './shared/contexts'
import { Layout, Disclaimer } from './shared'
import { LoginPage, RegisterPage } from './features/auth/pages'
import { MedicalProfilePage, MedicalLabResultsPage, EditProfilePage } from './features/medical/pages'
import { Recommendations } from './features/recommendations/components'
import { useAppNavigation } from './shared/hooks'
import type { Route } from './shared/types'

const KNOWN_ROUTES: Route[] = [
  'login',
  'register',
  'medical-profile',
  'lab-results',
  'recommendations',
  'edit-profile',
]

/** Mesaj de eroare centrat, cu o singură acțiune de revenire. */
const RouteNotice = ({
  message,
  detail,
  actionLabel,
  onAction,
}: {
  message: string
  detail?: string
  actionLabel: string
  onAction: () => void
}) => (
  <div className="w-full max-w-md text-center">
    <p className="mb-1 text-zinc-200">{message}</p>
    {detail && <p className="mb-2 text-sm text-zinc-500">{detail}</p>}
    <button
      type="button"
      onClick={onAction}
      className="mt-4 min-h-[44px] cursor-pointer rounded-lg bg-accent px-5 text-sm font-semibold text-accent-fg transition-colors hover:bg-accent-hover"
    >
      {actionLabel}
    </button>
  </div>
)

function App() {
  const { t } = useTranslation()
  const {
    route,
    authUser,
    medicalUser,
    isLoading,
    recommendationsRefreshKey,
    navigate,
    handleLogin,
    handleRegister,
    handleMedicalProfileComplete,
    handleLabResultsComplete,
    handleProfileUpdate,
    handleLogout,
  } = useAppNavigation()

  const showNav =
    (route === 'recommendations' || route === 'edit-profile' || route === 'lab-results') && !!medicalUser

  return (
    <ThemeProvider>
      <Layout route={route} showNav={showNav} onNavigate={navigate} onLogout={handleLogout}>
        {isLoading ? (
          <div className="w-full max-w-md py-16 text-center" role="status" aria-live="polite">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-white/10 border-t-accent" />
            <p className="text-sm text-zinc-400">{t('common.loading')}</p>
          </div>
        ) : (
          <>
            {route === 'login' && <LoginPage onNavigate={navigate} onLogin={handleLogin} />}
            {route === 'register' && <RegisterPage onNavigate={navigate} onRegister={handleRegister} />}
            {route === 'medical-profile' && authUser && (
              <MedicalProfilePage authUser={authUser} onComplete={handleMedicalProfileComplete} />
            )}
            {route === 'medical-profile' && !authUser && (
              <RouteNotice
                message={t('app.errors.noAuthUser')}
                actionLabel={t('common.goToLogin')}
                onAction={() => navigate('login')}
              />
            )}
            {route === 'lab-results' && medicalUser && (
              <MedicalLabResultsPage
                user={medicalUser}
                onComplete={handleLabResultsComplete}
                onBackToDashboard={() => navigate('recommendations')}
              />
            )}
            {route === 'lab-results' && !medicalUser && (
              <RouteNotice
                message={t('app.errors.noProfile')}
                actionLabel={t('common.createProfile')}
                onAction={() => navigate('medical-profile')}
              />
            )}
            {route === 'recommendations' && medicalUser && (
              <div className="w-full max-w-7xl">
                <Disclaimer />
                <Recommendations user={medicalUser} refreshKey={recommendationsRefreshKey} />
              </div>
            )}
            {route === 'recommendations' && !medicalUser && (
              <RouteNotice
                message={t('app.errors.noProfileForRecs')}
                actionLabel={t('common.createProfile')}
                onAction={() => navigate('medical-profile')}
              />
            )}
            {route === 'edit-profile' && medicalUser && (
              <EditProfilePage
                user={medicalUser}
                onUpdate={handleProfileUpdate}
                onNavigateBack={() => navigate('recommendations')}
                onNavigateToLabResults={() => navigate('lab-results')}
              />
            )}
            {route === 'edit-profile' && !medicalUser && (
              <RouteNotice
                message={t('app.errors.noProfile')}
                actionLabel={t('common.createProfile')}
                onAction={() => navigate('medical-profile')}
              />
            )}

            {/* Fallback pentru rute necunoscute */}
            {!KNOWN_ROUTES.includes(route) && (
              <RouteNotice
                message={t('app.errors.unknownRoute')}
                detail={t('app.errors.route', { route })}
                actionLabel={t('common.goToLogin')}
                onAction={() => navigate('login')}
              />
            )}
          </>
        )}
      </Layout>
    </ThemeProvider>
  )
}

export default App
