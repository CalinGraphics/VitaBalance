import React, { useState } from 'react'
import { ImagePlus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Alert, Avatar, Spinner } from '../../../shared/components'
import { profileService } from '../../../services/api'
import { ImageResizeError, resizeImageToDataUrl } from '../../../shared/utils/resizeImage'

interface ProfileAvatarEditorProps {
  name: string
  url: string | null | undefined
  onChange: (url: string | null) => void
}

type Status = { kind: 'success' | 'error'; message: string } | null

/** Schimbarea / ștergerea pozei de profil; se salvează imediat, separat de restul formularului. */
const ProfileAvatarEditor = ({ name, url, onChange }: ProfileAvatarEditorProps) => {
  const { t } = useTranslation()
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<Status>(null)

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || busy) return
    setStatus(null)
    setBusy(true)
    try {
      const image = await resizeImageToDataUrl(file)
      onChange(await profileService.uploadAvatar(image))
      setStatus({ kind: 'success', message: t('profile.avatar.saved') })
    } catch (err) {
      const key =
        err instanceof ImageResizeError
          ? err.reason === 'type'
            ? 'profile.avatar.errors.type'
            : 'profile.avatar.errors.read'
          : 'profile.avatar.errors.failed'
      setStatus({ kind: 'error', message: t(key) })
    } finally {
      setBusy(false)
    }
  }

  const handleRemove = async () => {
    if (busy) return
    setStatus(null)
    setBusy(true)
    try {
      await profileService.deleteAvatar()
      onChange(null)
      setStatus({ kind: 'success', message: t('profile.avatar.removed') })
    } catch {
      setStatus({ kind: 'error', message: t('profile.avatar.errors.failed') })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-labelledby="profile-avatar-title" className="mb-8 rounded-lg border border-line bg-white/[0.02] p-4">
      <h2 id="profile-avatar-title" className="field-label mb-3">
        {t('profile.avatar.title')}
      </h2>
      <div className="flex flex-wrap items-center gap-4">
        <Avatar name={name} url={url} size={72} alt={t('profile.avatar.alt', { name })} />
        <div className="flex flex-wrap items-center gap-2">
          <label
            className={`inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-dashed border-line-strong px-3.5 text-sm text-zinc-300 transition-colors focus-within:border-accent hover:border-accent hover:text-accent ${
              busy ? 'pointer-events-none opacity-60' : 'cursor-pointer'
            }`}
          >
            {busy ? <Spinner /> : <ImagePlus aria-hidden="true" className="h-4 w-4" />}
            <span>{busy ? t('profile.avatar.saving') : url ? t('profile.avatar.change') : t('profile.avatar.add')}</span>
            <input type="file" accept="image/*" className="sr-only" onChange={handleFile} disabled={busy} />
          </label>
          {url && !busy && (
            <button
              type="button"
              onClick={handleRemove}
              className="inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg px-3 text-sm text-zinc-400 transition-colors hover:text-red-300 touch-manipulation"
            >
              <Trash2 aria-hidden="true" className="h-4 w-4" />
              {t('profile.avatar.remove')}
            </button>
          )}
        </div>
      </div>
      {status && (
        <Alert variant={status.kind} className="mt-4">
          {status.message}
        </Alert>
      )}
    </section>
  )
}

export default ProfileAvatarEditor
