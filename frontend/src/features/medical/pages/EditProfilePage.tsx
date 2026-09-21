import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, FlaskConical, Save, UserCog } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { GlassCard, PrimaryButton, PageHeader, Alert, Spinner } from '../../../shared/components'
import { profileService } from '../../../services/api'
import { regenerateRecommendationsAfterSave } from '../../recommendations/utils/regenerateAfterSave'
import type { User } from '../../../shared/types'
import { useProfileForm } from '../hooks/useProfileForm'
import ProfileFormFields from '../components/ProfileFormFields'

interface EditProfilePageProps {
  user: User
  onUpdate: (user: User) => void
  onNavigateBack: () => void
  onNavigateToLabResults?: () => void
}

const EditProfilePage = ({ user, onUpdate, onNavigateBack, onNavigateToLabResults }: EditProfilePageProps) => {
  const { t } = useTranslation()
  const form = useProfileForm({ user })
  const [loading, setLoading] = useState(false)
  const [loadingNote, setLoadingNote] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const redirectTimer = useRef<number | undefined>(undefined)

  // Nu lăsa redirectul programat să se execute după ce pagina a fost părăsită.
  useEffect(() => () => window.clearTimeout(redirectTimer.current), [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (loading) return
    setError(null)
    setSuccess(false)

    const result = form.buildPayload()
    if (result.error !== undefined) {
      setError(result.error)
      return
    }

    setLoading(true)
    try {
      const response = await profileService.update(user.id || 0, result.payload)

      // Actualizează starea utilizatorului imediat după salvare,
      // indiferent dacă regenerarea recomandărilor reușește sau nu
      onUpdate({ ...user, ...response })

      // Regenerare recomandări — best-effort, nu blochează navigarea
      if (user.id) {
        try {
          setLoadingNote(t('profile.edit.regenerating'))
          await regenerateRecommendationsAfterSave(user.id)
        } catch (recErr) {
          console.error('Eroare la regenerarea recomandărilor:', recErr)
        }
        setLoadingNote(null)
      }

      setSuccess(true)
      redirectTimer.current = window.setTimeout(onNavigateBack, 1500)
    } catch (err: unknown) {
      console.error('Eroare la actualizarea profilului:', err)
      setError(err instanceof Error && err.message ? err.message : t('profile.errors.updateFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-3xl">
      <GlassCard className="mx-auto w-full">
        <button
          type="button"
          onClick={onNavigateBack}
          className="-ml-1 mb-4 inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg px-1 text-sm font-medium text-zinc-400 transition-colors hover:text-accent touch-manipulation"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {t('profile.edit.backToRecs')}
        </button>

        <PageHeader Icon={UserCog} title={t('profile.edit.title')} subtitle={t('profile.edit.subtitle')} />

        {error && <Alert variant="error" className="mb-5">{error}</Alert>}
        {success && <Alert variant="success" className="mb-5">{t('profile.edit.success')}</Alert>}

        <form onSubmit={handleSubmit} noValidate>
          <ProfileFormFields form={form} />

          {onNavigateToLabResults && (
            <div className="mt-6 rounded-lg border border-line bg-white/[0.02] p-4">
              <p className="mb-3 text-sm leading-relaxed text-zinc-400">{t('profile.edit.labsPrompt')}</p>
              <button
                type="button"
                onClick={onNavigateToLabResults}
                className="inline-flex min-h-[44px] cursor-pointer items-center justify-center gap-2 rounded-lg border border-accent-border px-4 text-sm font-medium text-accent transition-colors hover:bg-accent-soft touch-manipulation"
              >
                <FlaskConical aria-hidden="true" className="h-4 w-4" />
                {t('profile.edit.labsButton')}
              </button>
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <PrimaryButton type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Spinner />
                  <span>{loadingNote || t('profile.edit.saving')}</span>
                </>
              ) : (
                <>
                  <Save aria-hidden="true" className="h-4 w-4" />
                  <span>{t('profile.edit.save')}</span>
                </>
              )}
            </PrimaryButton>
            <PrimaryButton variant="secondary" onClick={onNavigateBack}>
              {t('common.cancel')}
            </PrimaryButton>
          </div>
        </form>
      </GlassCard>
    </div>
  )
}

export default EditProfilePage
