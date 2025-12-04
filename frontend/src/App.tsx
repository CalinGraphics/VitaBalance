import { ThemeProvider } from './shared/contexts'
import { Layout, Disclaimer } from './shared'
import { LoginPage, RegisterPage } from './features/auth/pages'
import { MedicalProfilePage, MedicalLabResultsPage } from './features/medical/pages'
import { Recommendations } from './features/recommendations/components'
import { useAppNavigation } from './shared/hooks'

import { useState, useEffect } from 'react'
import { supabase } from '../utils/supabase'

function Page() {
  const [todos, setTodos] = useState([])

  useEffect(() => {
    function getTodos() {
      const { data: todos } = await supabase.from('todos').select()

      if (todos.length > 1) {
        setTodos(todos)
      }
    }

    getTodos()
  }, [])

  return (
    <div>
      {todos.map((todo) => (
        <li key={todo}>{todo}</li>
      ))}
    </div>
  )
}
export default Page

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

