import { ThemeProvider } from './shared/contexts'
import { Layout, Disclaimer } from './shared'
import { LoginPage, RegisterPage } from './features/auth/pages'
import { MedicalProfilePage, MedicalLabResultsPage } from './features/medical/pages'
import { Recommendations } from './features/recommendations/components'
import { useAppNavigation } from './shared/hooks'

function App() {
  const {
    route,
    authUser,
    medicalUser,
    navigate,
    handleLogin,
    handleRegister,
    handleMedicalProfileComplete,
    handleLabResultsComplete,
    handleLogout,
  } = useAppNavigation()

  return (
    <ThemeProvider>
      <Layout 
        onLogout={handleLogout}
        showLogout={route === 'recommendations' && !!medicalUser}
      >
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
        {route === 'medical-profile' && authUser && (
          <MedicalProfilePage
            authUser={authUser}
            onComplete={handleMedicalProfileComplete}
          />
        )}
        {route === 'lab-results' && medicalUser && (
          <MedicalLabResultsPage
            user={medicalUser}
            onComplete={handleLabResultsComplete}
          />
        )}
        {route === 'recommendations' && medicalUser && (
          <div className="w-full max-w-7xl">
            <Disclaimer />
            <Recommendations user={medicalUser} />
          </div>
        )}
      </Layout>
    </ThemeProvider>
  )
}

export default App

