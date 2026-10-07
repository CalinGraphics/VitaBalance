import { useState, useCallback, useEffect } from 'react'
import type { Route, AuthUser, User } from '../types'
import { isAxiosError } from 'axios'
import { profileService, authService } from '../../services/api'
import { getToken, setSession, clearToken, type StoredSession } from '../../services/authStorage'

// Un profil medical este considerat "complet" doar dacă are valorile de bază setate.
// Un cont proaspăt înregistrat are câmpurile numerice 0 / implicite,
// așa că îl trimitem prin ecranul de creare profil.
const hasCompleteMedicalProfile = (profile: User | null | undefined): boolean => {
  if (!profile || !profile.id) return false
  if (!profile.age || profile.age <= 0) return false
  if (!profile.weight || profile.weight <= 0) return false
  if (!profile.height || profile.height <= 0) return false
  if (!profile.sex || !profile.activity_level || !profile.diet_type) return false
  return true
}

export const useAppNavigation = () => {
  const [route, setRoute] = useState<Route>('login')
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [medicalUser, setMedicalUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [recommendationsRefreshKey, setRecommendationsRefreshKey] = useState(0)
  /** Mesaj (cheie i18n) afișat o dată deasupra paginii, ex. poza nu a putut fi urcată după înregistrare. */
  const [notice, setNotice] = useState<string | null>(null)

  const navigate = useCallback((newRoute: Route) => {
    setRoute(newRoute)
  }, [])

  const handleLogin = useCallback(async (loggedUser: AuthUser, session?: StoredSession) => {
    if (session?.access_token) setSession(session)
    setIsLoading(true)
    setAuthUser(loggedUser)
    
    try {
      // Verifică dacă utilizatorul are deja profil medical
      try {
        const existingProfile = await profileService.getByEmail(loggedUser.email)
        setAuthUser({ ...loggedUser, avatarUrl: existingProfile?.avatar_url ?? null })
        
        if (hasCompleteMedicalProfile(existingProfile)) {
          // Are deja profil complet, merge direct la recomandări
          setMedicalUser(existingProfile)
          setRoute('recommendations')
        } else {
          // Nu are profil complet (cont nou) – merge la crearea profilului
          setMedicalUser(null)
          setRoute('medical-profile')
        }
      } catch (error: unknown) {
        const statusCode = isAxiosError(error)
          ? error.response?.status
          : (error as { status?: number }).status
        if (statusCode === 404) {
          // Nu are profil, merge la crearea profilului
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

  const handleRegister = useCallback(
    async (newUser: AuthUser, session?: StoredSession, avatar?: string | null) => {
      if (session?.access_token) setSession(session)
      setAuthUser(newUser)
      setRoute('medical-profile')
      if (!avatar) return
      // Poza se urcă abia acum: endpoint-ul cere sesiunea contului tocmai creat.
      try {
        const avatarUrl = await profileService.uploadAvatar(avatar)
        setAuthUser((prev) => (prev ? { ...prev, avatarUrl } : prev))
      } catch (err) {
        console.error('Poza de profil nu a putut fi urcată după înregistrare:', err)
        setNotice('profile.avatar.errors.uploadAfterSignup')
      }
    },
    []
  )

  const handleMedicalProfileComplete = useCallback((user: User) => {
    setMedicalUser(user)
    setRoute('lab-results')
  }, [])

  const handleLabResultsComplete = useCallback(() => {
    setRecommendationsRefreshKey((k) => k + 1)
    setRoute('recommendations')
  }, [])

  /** O zi nouă în jurnal schimbă stările recente, deci și recomandările (hash-ul intrărilor din backend). */
  const handleCheckinSaved = useCallback(() => {
    setRecommendationsRefreshKey((k) => k + 1)
  }, [])

  const handleProfileUpdate = useCallback((updatedUser: User) => {
    setMedicalUser(updatedUser)
    setAuthUser((prev) => (prev ? { ...prev, fullName: updatedUser.name || prev.fullName } : prev))
    setRecommendationsRefreshKey((k) => k + 1)
  }, [])

  /** Schimbarea pozei nu atinge datele medicale, deci nu reîmprospătează recomandările. */
  const handleAvatarChange = useCallback((avatarUrl: string | null) => {
    setAuthUser((prev) => (prev ? { ...prev, avatarUrl } : prev))
    setMedicalUser((prev) => (prev ? { ...prev, avatar_url: avatarUrl } : prev))
  }, [])

  const handleLogout = useCallback(() => {
    if (getToken()) void authService.logout().finally(clearToken)
    else clearToken()
    setAuthUser(null)
    setMedicalUser(null)
    setNotice(null)
    setRoute('login')
  }, [])

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    authService
      .me()
      .then((me: { email: string; fullName: string; avatarUrl?: string | null }) => {
        setAuthUser({
          email: me.email,
          fullName: me.fullName,
          avatarUrl: me.avatarUrl ?? null,
        })
        return profileService.getByEmail(me.email)
      })
      .then((existingProfile: User) => {
        if (hasCompleteMedicalProfile(existingProfile)) {
          setMedicalUser(existingProfile)
          setRoute('recommendations')
        } else {
          setMedicalUser(null)
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
    handleCheckinSaved,
    handleAvatarChange,
    handleLogout,
    notice,
    dismissNotice: () => setNotice(null),
  }
}

