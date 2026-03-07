import { useState, useCallback, useEffect } from 'react'
import type { Route, AuthUser, User } from '../types'
import { profileService, authService } from '../../services/api'
import { getToken, setToken, clearToken } from '../../services/authStorage'

export const useAppNavigation = () => {
  const [route, setRoute] = useState<Route>('login')
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [medicalUser, setMedicalUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [recommendationsRefreshKey, setRecommendationsRefreshKey] = useState(0)

  const navigate = useCallback((newRoute: Route) => {
    setRoute(newRoute)
  }, [])

  const handleLogin = useCallback(async (loggedUser: AuthUser, accessToken?: string) => {
    if (accessToken) setToken(accessToken)
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
  }, [])

  const handleRegister = useCallback((newUser: AuthUser, accessToken?: string) => {
    if (accessToken) setToken(accessToken)
    setAuthUser(newUser)
    setRoute('medical-profile')
  }, [])

  const handleMedicalProfileComplete = useCallback((user: User) => {
    setMedicalUser(user)
    setRoute('lab-results')
  }, [])

  const handleLabResultsComplete = useCallback(() => {
    setRecommendationsRefreshKey((k) => k + 1)
    setRoute('recommendations')
  }, [])

  const handleProfileUpdate = useCallback((updatedUser: User) => {
    setMedicalUser(updatedUser)
    setRecommendationsRefreshKey((k) => k + 1)
    setRoute('recommendations')
  }, [])

  const handleLogout = useCallback(() => {
    clearToken()
    setAuthUser(null)
    setMedicalUser(null)
    setRoute('login')
  }, [])

  useEffect(() => {
    // Token din query (?token=) sau din hash (#token=) – pentru compatibilitate cu diverse redirecturi.
    // Îl salvăm și în sessionStorage ca fallback, pentru cazuri în care URL-ul este modificat de browser/hosting.
    const queryParams = new URLSearchParams(window.location.search)
    const hashPart = window.location.hash.replace(/^#/, '').replace(/^\?/, '')
    const hashParams = new URLSearchParams(hashPart)
    const magicToken = queryParams.get('token') || hashParams.get('token')
    if (magicToken) {
      try {
        sessionStorage.setItem('vitabalance_magic_token', magicToken)
      } catch {
        // ignoră dacă sessionStorage nu este disponibil
      }
      setRoute('auth-verify')
      setIsLoading(false)
      return
    }
    const token = getToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    authService
      .me()
      .then((me: AuthUser) => {
        setAuthUser(me)
        return profileService.getByEmail(me.email)
      })
      .then((existingProfile: User) => {
        if (existingProfile?.id) {
          setMedicalUser(existingProfile)
          setRoute('recommendations')
        } else {
          setRoute('medical-profile')
        }
      })
      .catch(() => {
        setRoute('login')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  return {
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
  }
}

