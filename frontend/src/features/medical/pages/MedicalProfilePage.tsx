import React, { useState } from 'react'
import { ArrowRight, UserPlus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, PrimaryButton, PageHeader, Alert, Spinner } from '../../../shared/components'
import { profileService } from '../../../services/api'
import type { User, AuthUser } from '../../../shared/types'
import { useProfileForm } from '../hooks/useProfileForm'
import ProfileFormFields from '../components/ProfileFormFields'

interface MedicalProfilePageProps {
  authUser: AuthUser
  onComplete: (user: User) => void
}

const MedicalProfilePage = ({ authUser, onComplete }: MedicalProfilePageProps) => {
  const { t } = useTranslation()
  const form = useProfileForm({ email: authUser.email })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return
    setError(null)

    const result = form.buildPayload()
    if (result.error !== undefined) {
      setError(result.error)
      return
    }

    setLoading(true)
    try {
      const response = await profileService.create(result.payload)
      onComplete(response)
    } catch (err: unknown) {
      console.error('Eroare la salvarea profilului:', err)
      setError(err instanceof Error && err.message ? err.message : t('profile.errors.saveFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-3xl">
      <GlassCard className="mx-auto w-full">
        <PageHeader
          Icon={UserPlus}
          title={t('profile.create.title')}
          subtitle={t('profile.create.subtitle')}
        />

        {error && <Alert variant="error" className="mb-5">{error}</Alert>}

        <form onSubmit={handleSubmit} noValidate>
          <ProfileFormFields form={form} />

          <div className="mt-8">
            <PrimaryButton type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Spinner />
                  <span>{t('profile.create.saving')}</span>
                </>
              ) : (
                <>
                  <span>{t('profile.create.submit')}</span>
                  <ArrowRight aria-hidden="true" className="h-4 w-4" />
                </>
              )}
            </PrimaryButton>
          </div>
        </form>
      </GlassCard>
    </div>
  )
}

export default MedicalProfilePage
