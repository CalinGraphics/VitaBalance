import React, { useEffect, useState } from 'react'
import { GlassCard } from '../../../shared/components'
import { authService } from '../../../services/api'
import { setToken } from '../../../services/authStorage'
import type { AuthUser } from '../../../shared/types'

interface AuthVerifyPageProps {
  onLogin: (user: AuthUser, accessToken?: string) => void
  onNavigate: (route: 'login') => void
}

const AuthVerifyPage: React.FC<AuthVerifyPageProps> = ({ onLogin, onNavigate }) => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [errorMessage, setErrorMessage] = useState<string>('')

  useEffect(() => {
    // Token din query (?token=) sau din hash (#?token=). Dacă nu există în URL,
    // încercăm să îl luăm din sessionStorage (setat în useAppNavigation).
    const queryParams = new URLSearchParams(window.location.search)
    const hashPart = window.location.hash.replace(/^#/, '').replace(/^\?/, '')
    const hashParams = new URLSearchParams(hashPart)
    const urlToken = queryParams.get('token') || hashParams.get('token')
    let token = urlToken
    if (!token) {
      try {
        token = sessionStorage.getItem('vitabalance_magic_token') || ''
      } catch {
        token = ''
      }
    }
    if (!token) {
      setStatus('error')
      setErrorMessage('Link invalid: lipsește tokenul.')
      return
    }
    authService
      .verifyMagicLink(token)
      .then((data: { email: string; fullName: string; bio: string; access_token: string }) => {
        setToken(data.access_token)
        try {
          sessionStorage.removeItem('vitabalance_magic_token')
        } catch {
          // ignoră
        }
        onLogin(
          {
            fullName: data.fullName,
            email: data.email,
            bio: data.bio,
            avatarUrl: null,
          },
          data.access_token
        )
        setStatus('success')
        window.history.replaceState({}, '', window.location.pathname)
      })
      .catch((err: any) => {
        setStatus('error')
        setErrorMessage(err?.message || 'Link invalid, expirat sau deja folosit.')
      })
  }, [onLogin])

  if (status === 'loading') {
    return (
      <GlassCard>
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-neonCyan mb-4" />
          <p className="text-slate-300">Se verifică linkul de autentificare...</p>
        </div>
      </GlassCard>
    )
  }

  if (status === 'error') {
    return (
      <GlassCard>
        <div className="text-center py-8">
          <p className="text-red-400 mb-4">{errorMessage}</p>
          <button
            onClick={() => onNavigate('login')}
            className="px-4 py-2 bg-neonCyan text-black rounded-lg hover:bg-neonMagenta transition"
          >
            Mergi la autentificare
          </button>
        </div>
      </GlassCard>
    )
  }

  return (
    <GlassCard>
      <div className="text-center py-8">
        <p className="text-neonCyan mb-4">Autentificare reușită. Se încarcă...</p>
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-neonCyan" />
      </div>
    </GlassCard>
  )
}

export default AuthVerifyPage
