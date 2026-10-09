import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ImagePlus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import type { AuthUser, Route } from '../../../shared/types';
import { authService } from '../../../services/api';
import type { StoredSession } from '../../../services/authStorage';
import { extractErrorCode, extractErrorMessage } from '../../../shared/utils/apiErrors';
import AuthHero, { AuthCardGlow, BrandName } from '../components/AuthHero';
import { ImageResizeError, resizeImageToDataUrl } from '../../../shared/utils/resizeImage';

interface RegisterPageProps {
  onNavigate: (route: Route) => void;
  /** `avatar`: poza aleasă, deja micșorată (data URL); se urcă după crearea contului. */
  onRegister: (user: AuthUser, session?: StoredSession, avatar?: string | null) => void;
}

type FieldErrors = {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Erori cunoscute de la backend care aparțin unui câmp anume. */
const ERROR_CODE_FIELD: Record<string, keyof FieldErrors> = {
  emailTaken: 'email',
  legacyProfileLocked: 'email',
  emailRequired: 'email',
  invalidEmail: 'email',
  fullNameRequired: 'fullName',
  passwordRequired: 'password',
  passwordBlank: 'password',
  passwordTooShort: 'password',
};

const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigate, onRegister }) => {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    avatarPreview: null as string | null,
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange =
    (field: 'fullName' | 'email' | 'password' | 'confirmPassword') =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
    };

  // Poza e micșorată aici (256 px) și trimisă la server după crearea contului (useAppNavigation).
  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setAvatarError(null);
    try {
      const avatarPreview = await resizeImageToDataUrl(file);
      setForm((prev) => ({ ...prev, avatarPreview }));
    } catch (err) {
      const reason = err instanceof ImageResizeError ? err.reason : 'read';
      setAvatarError(t(reason === 'type' ? 'profile.avatar.errors.type' : 'profile.avatar.errors.read'));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    const newErrors: FieldErrors = {};
    if (!form.fullName.trim()) newErrors.fullName = t('apiErrors.fullNameRequired');
    if (!form.email.trim()) newErrors.email = t('apiErrors.emailRequired');
    else if (!EMAIL_PATTERN.test(form.email.trim())) newErrors.email = t('apiErrors.invalidEmail');
    if (form.password.length < 6) newErrors.password = t('apiErrors.passwordTooShort');
    if (form.password !== form.confirmPassword) newErrors.confirmPassword = t('auth.register.passwordMismatch');

    setErrors(newErrors);
    setFormError(null);
    if (Object.keys(newErrors).length > 0) return;

    setIsLoading(true);
    try {
      const session = await authService.register(form.email, form.password, form.fullName);
      onRegister(
        { email: session.email, fullName: session.fullName, avatarUrl: null },
        session,
        form.avatarPreview
      );
    } catch (err: unknown) {
      const message = extractErrorMessage(err);
      const code = extractErrorCode(err);
      const field = code ? ERROR_CODE_FIELD[code] : undefined;
      if (field) setErrors({ [field]: message });
      else setFormError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full max-w-full flex-col items-center justify-center gap-8 md:flex-row-reverse md:gap-20">
      <AuthHero
        eyebrow={t('auth.register.eyebrow')}
        title={<>{t('auth.register.heroTitle')} <BrandName /></>}
        text={t('auth.register.heroText')}
        align="right"
        steps
      />

      <AuthCardGlow>
        <GlassCard className="w-full max-w-full">
          <div className="mb-6">
            <h2 className="text-xl font-semibold tracking-tight text-zinc-50">{t('auth.register.cardTitle')}</h2>
            <p className="mt-1 text-sm leading-relaxed text-zinc-400">{t('auth.register.cardSubtitle')}</p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <InputField
              label={t('auth.fields.fullName')}
              value={form.fullName}
              onChange={handleChange('fullName')}
              placeholder={t('auth.fields.fullNamePlaceholder')}
              error={errors.fullName}
              autoComplete="name"
            />
            <InputField
              label={t('auth.fields.email')}
              type="email"
              value={form.email}
              onChange={handleChange('email')}
              placeholder={t('auth.fields.emailPlaceholder')}
              error={errors.email}
              autoComplete="email"
              inputMode="email"
            />
            <InputField
              label={t('auth.fields.password')}
              type="password"
              value={form.password}
              onChange={handleChange('password')}
              placeholder={t('auth.fields.passwordPlaceholder')}
              error={errors.password}
              hint={t('auth.register.passwordHint')}
              autoComplete="new-password"
            />
            <InputField
              label={t('auth.fields.confirmPassword')}
              type="password"
              value={form.confirmPassword}
              onChange={handleChange('confirmPassword')}
              placeholder={t('auth.fields.confirmPasswordPlaceholder')}
              error={errors.confirmPassword}
              autoComplete="new-password"
            />

            <div className="mb-4">
              <span className="field-label">{t('auth.register.avatarLabel')}</span>
              <div className="flex items-center gap-4">
                <label className="inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border border-dashed border-line-strong px-3.5 text-sm text-zinc-300 transition-colors focus-within:border-accent hover:border-accent hover:text-accent">
                  <ImagePlus aria-hidden="true" className="h-4 w-4" />
                  <span>{t('auth.register.avatarChoose')}</span>
                  <input type="file" accept="image/*" className="sr-only" onChange={handleAvatarChange} />
                </label>
                {form.avatarPreview && (
                  <>
                    <motion.img
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      src={form.avatarPreview}
                      alt={t('auth.register.avatarAlt')}
                      className="h-12 w-12 rounded-full border border-line-strong object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, avatarPreview: null }))}
                      className="min-h-[44px] cursor-pointer px-1 text-sm text-zinc-400 transition-colors hover:text-red-300 touch-manipulation"
                    >
                      {t('auth.register.avatarRemove')}
                    </button>
                  </>
                )}
              </div>
              {avatarError ? (
                <p role="alert" className="mt-1.5 text-xs text-red-400">{avatarError}</p>
              ) : (
                <p className="mt-1.5 text-xs text-zinc-500">{t('auth.register.avatarHint')}</p>
              )}
            </div>

            {formError && (
              <p
                role="alert"
                className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300"
              >
                {formError}
              </p>
            )}

            <div className="mt-6">
              <PrimaryButton type="submit" disabled={isLoading}>
                {isLoading ? t('auth.register.submitting') : t('auth.register.submit')}
              </PrimaryButton>
            </div>
          </form>

          <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5 text-sm">
            <span className="text-zinc-400">{t('auth.register.haveAccount')}</span>
            <button
              type="button"
              onClick={() => onNavigate('login')}
              className="min-h-[44px] cursor-pointer px-1 font-semibold text-accent transition-colors hover:text-accent-hover touch-manipulation"
            >
              {t('auth.register.backToLogin')}
            </button>
          </div>
        </GlassCard>
      </AuthCardGlow>
    </div>
  );
};

export default RegisterPage;
