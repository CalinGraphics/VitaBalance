import { useState, useCallback, useEffect } from 'react'
import type { Route, AuthUser, User } from '../types'

export const useAppNavigation = () => {
  const [route, setRoute] = useState<Route>('login')
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [medicalUser, setMedicalUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const navigate = useCallback((newRoute: Route) => {
    setRoute(newRoute)
  }, [])

<<<<<<< Updated upstream
  const handleLogin = useCallback((loggedUser: AuthUser) => {
    setAuthUser(loggedUser)
    setRoute('medical-profile')
=======
  const handleLogin = useCallback(async (loggedUser: AuthUser) => {
    if (import.meta.env.DEV) {
      console.log('handleLogin called with:', loggedUser)
    }
    setIsLoading(true)
    setAuthUser(loggedUser)
    
    try {
      // Verifică dacă utilizatorul are deja profil medical
      try {
        if (import.meta.env.DEV) {
          console.log('Caută profil pentru email:', loggedUser.email)
        }
        const existingProfile = await profileService.getByEmail(loggedUser.email)
        if (import.meta.env.DEV) {
          console.log('Profil găsit:', existingProfile)
        }
        
        if (existingProfile && existingProfile.id) {
          // Are deja profil, merge direct la recomandări
          if (import.meta.env.DEV) {
            console.log('Setăm medicalUser și route la recommendations')
          }
          setMedicalUser(existingProfile)
          setRoute('recommendations')
        } else {
          // Nu are profil, merge la crearea profilului
          if (import.meta.env.DEV) {
            console.log('Utilizatorul nu are profil medical, va crea unul nou')
          }
          setRoute('medical-profile')
        }
      } catch (error: any) {
        // Verifică dacă eroarea este 404 (profilul nu există)
        const statusCode = error.response?.status || error.status
        if (import.meta.env.DEV) {
          console.log('Eroare la căutarea profilului, status:', statusCode, error)
        }
        if (statusCode === 404) {
          // Nu are profil, merge la crearea profilului
          if (import.meta.env.DEV) {
            console.log('Utilizatorul nu are profil medical (404), va crea unul nou')
          }
          setRoute('medical-profile')
        } else {
          // Altă eroare - loghează și merge la crearea profilului
          console.error('Eroare la verificarea profilului:', error)
          setRoute('medical-profile')
        }
      }
    } catch (err) {
      console.error('Eroare neașteptată în handleLogin:', err)
      setRoute('medical-profile')
    } finally {
      setIsLoading(false)
    }
>>>>>>> Stashed changes
  }, [])

  const handleRegister = useCallback((newUser: AuthUser) => {
    setAuthUser(newUser)
    setRoute('medical-profile')
  }, [])

  const handleMedicalProfileComplete = useCallback((user: User) => {
    setMedicalUser(user)
    setRoute('lab-results')
  }, [])

  const handleLabResultsComplete = useCallback(() => {
    setRoute('recommendations')
  }, [])

  const handleLogout = useCallback(() => {
    setAuthUser(null)
    setMedicalUser(null)
    setRoute('login')
  }, [])

  return {
    route,
    authUser,
    medicalUser,
    isLoading,
    navigate,
    handleLogin,
    handleRegister,
    handleMedicalProfileComplete,
    handleLabResultsComplete,
    handleLogout,
  }
}

