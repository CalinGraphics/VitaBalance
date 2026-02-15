import { ThemeProvider } from './shared/contexts'
import { Layout, Disclaimer } from './shared'
import { LoginPage, RegisterPage, AuthVerifyPage } from './features/auth/pages'
import { MedicalProfilePage, MedicalLabResultsPage, EditProfilePage } from './features/medical/pages'
import { Recommendations } from './features/recommendations/components'
import { useAppNavigation } from './shared/hooks'

function App() {
  const {
    route,
    authUser,
    medicalUser,
    isLoading,
    navigate,
    handleLogin,
    handleRegister,
    handleMedicalProfileComplete,
    handleLabResultsComplete,
    handleProfileUpdate,
    handleLogout,
  } = useAppNavigation()

  // Debug logging only in development
  if (import.meta.env.DEV) {
    console.log('App render - Route:', route, 'AuthUser:', !!authUser, 'MedicalUser:', !!medicalUser, 'Loading:', isLoading)
  }

  return (
    <ThemeProvider>
      <Layout 
        onLogout={handleLogout}
        showLogout={route === 'recommendations' && !!medicalUser}
        onProfileClick={() => navigate('edit-profile')}
        showProfile={route === 'recommendations' && !!medicalUser}
      >
        {/* Loading state - prioritate maximă */}
        {isLoading ? (
          <div className="w-full max-w-md text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neonCyan mb-4"></div>
            <p className="text-slate-300">Se încarcă...</p>
          </div>
        ) : (
          <>
            {route === 'login' && (
              <LoginPage 
                onNavigate={navigate} 
                onLogin={handleLogin} 
              />
            )}
            {route === 'register' && (
              <RegisterPage 
                onNavigate={navigate} 
                onRegister={handleRegister} 
              />
            )}
            {route === 'auth-verify' && (
              <AuthVerifyPage
                onLogin={handleLogin}
                onNavigate={navigate}
              />
            )}
            {route === 'medical-profile' && authUser && (
              <MedicalProfilePage
                authUser={authUser}
                onComplete={handleMedicalProfileComplete}
              />
            )}
            {route === 'medical-profile' && !authUser && (
              <div className="w-full max-w-md text-center">
                <p className="text-red-400 mb-4">Eroare: Nu există utilizator autentificat</p>
                <button
                  onClick={() => navigate('login')}
                  className="mt-4 text-neonCyan hover:text-neonMagenta transition"
                >
                  Mergi la login
                </button>
              </div>
            )}
            {route === 'lab-results' && medicalUser && (
              <MedicalLabResultsPage
                user={medicalUser}
                onComplete={handleLabResultsComplete}
              />
            )}
            {route === 'lab-results' && !medicalUser && (
              <div className="w-full max-w-md text-center">
                <p className="text-red-400 mb-4">Eroare: Profil medical lipsă</p>
                <button
                  onClick={() => navigate('medical-profile')}
                  className="mt-4 text-neonCyan hover:text-neonMagenta transition"
                >
                  Creează profil
                </button>
              </div>
            )}
            {route === 'recommendations' && medicalUser && (
              <div className="w-full max-w-7xl">
                <Disclaimer />
                <Recommendations user={medicalUser} />
              </div>
            )}
            {route === 'recommendations' && !medicalUser && (
              <div className="w-full max-w-md text-center">
                <p className="text-red-400 mb-4">Eroare: Profil medical lipsă pentru recomandări</p>
                <button
                  onClick={() => navigate('medical-profile')}
                  className="mt-4 text-neonCyan hover:text-neonMagenta transition"
                >
                  Creează profil
                </button>
              </div>
            )}
            {route === 'edit-profile' && medicalUser && (
              <EditProfilePage
                user={medicalUser}
                onUpdate={handleProfileUpdate}
                onNavigateBack={() => navigate('recommendations')}
              />
            )}
            {route === 'edit-profile' && !medicalUser && (
              <div className="w-full max-w-md text-center">
                <p className="text-red-400 mb-4">Eroare: Profil medical lipsă</p>
                <button
                  onClick={() => navigate('medical-profile')}
                  className="mt-4 text-neonCyan hover:text-neonMagenta transition"
                >
                  Creează profil
                </button>
              </div>
            )}
            
            {/* Fallback pentru rute necunoscute */}
            {!['login', 'register', 'auth-verify', 'medical-profile', 'lab-results', 'recommendations', 'edit-profile'].includes(route) && (
              <div className="w-full max-w-md text-center">
                <p className="text-slate-300 mb-4">Rută necunoscută</p>
                <p className="text-slate-500 text-sm mb-4">Route: {route}</p>
                <button
                  onClick={() => navigate('login')}
                  className="mt-4 px-4 py-2 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition"
                >
                  Mergi la login
                </button>
              </div>
            )}
          </>
        )}
      </Layout>
    </ThemeProvider>
  )
}

export default App

