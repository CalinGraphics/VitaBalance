import { useState, useCallback } from 'react'
import type { Route, AuthUser, User } from '../types'

export const useAppNavigation = () => {
  const [route, setRoute] = useState<Route>('login')
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [medicalUser, setMedicalUser] = useState<User | null>(null)

  const navigate = useCallback((newRoute: Route) => {
    setRoute(newRoute)
  }, [])

  const handleLogin = useCallback((loggedUser: AuthUser) => {
    setAuthUser(loggedUser)
    setRoute('medical-profile')
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
    navigate,
    handleLogin,
    handleRegister,
    handleMedicalProfileComplete,
    handleLabResultsComplete,
    handleLogout,
  }
}

