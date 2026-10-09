import React, { useState } from 'react'
import { Camera, ImagePlus, Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Alert, Avatar, Spinner } from '../../../shared/components'
import { profileService } from '../../../services/api'
import { ImageResizeError, resizeImageToDataUrl } from '../../../shared/utils/resizeImage'

interface ProfileAvatarEditorProps {
  name: string
  email?: string
  url: string | null | undefined
  onChange: (url: string | null) => void
}

type Status = { kind: 'success' | 'error'; message: string } | null

/** Schimbarea / ștergerea pozei de profil; se salvează imediat, separat de restul formularului. */
const ProfileAvatarEditor = ({ name, email, url, onChange }: ProfileAvatarEditorProps) => {
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

  const pickerClass = busy ? 'pointer-events-none' : 'cursor-pointer'

  return (
    <section aria-labelledby="profile-avatar-title" className="mb-8 rounded-lg border border-line bg-white/[0.02] p-4 sm:p-5">
      <h2 id="profile-avatar-title" className="sr-only">
        {t('profile.avatar.title')}
      </h2>
      <div className="flex items-center gap-4 sm:gap-5">
        <div className="group relative flex-shrink-0">
          {/* Click pe poză = alegi alta; camera apare la hover/focus. */}
          <label className={`relative block rounded-full focus-within:ring-2 focus-within:ring-accent/70 focus-within:ring-offset-2 focus-within:ring-offset-surface ${pickerClass}`}
            title={url ? t('profile.avatar.change') : t('profile.avatar.add')}>
            <Avatar name={name} url={url} size={84} alt={t('profile.avatar.alt', { name })} />
            <span aria-hidden="true"
              className={`absolute inset-0 flex items-center justify-center rounded-full bg-black/55 text-white transition-opacity duration-200 ${
                busy ? 'opacity-100' : 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
              }`}>
              {busy ? <Spinner /> : <Camera className="h-6 w-6" />}
            </span>
            <span className="sr-only">{url ? t('profile.avatar.change') : t('profile.avatar.add')}</span>
            <input type="file" accept="image/*" className="sr-only" onChange={handleFile} disabled={busy} />
          </label>
          {url && !busy && (
            <button
              type="button"
              onClick={handleRemove}
              aria-label={t('profile.avatar.remove')}
              title={t('profile.avatar.remove')}
              className="absolute -right-1 -top-1 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border-2 border-surface bg-zinc-800 text-zinc-300 shadow-pop transition-colors hover:bg-red-500 hover:text-white focus-visible:bg-red-500 focus-visible:text-white touch-manipulation"
            >
              <Trash2 aria-hidden="true" className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">{name}</p>
          {email && email !== name && <p className="mt-0.5 truncate text-sm text-zinc-400">{email}</p>}
          <label className={`mt-2 inline-flex min-h-[36px] items-center gap-1.5 rounded-lg text-sm font-medium text-accent transition-colors hover:text-accent-hover focus-within:underline ${pickerClass}`}>
            <ImagePlus aria-hidden="true" className="h-4 w-4" />
            <span>{busy ? t('profile.avatar.saving') : url ? t('profile.avatar.change') : t('profile.avatar.add')}</span>
            <input type="file" accept="image/*" className="sr-only" onChange={handleFile} disabled={busy} />
          </label>
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
