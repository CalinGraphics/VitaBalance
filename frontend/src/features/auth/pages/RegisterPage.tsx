import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ImagePlus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import type { AuthUser, Route } from '../../../shared/types';
import { authService } from '../../../services/api';
import { extractErrorCode, extractErrorMessage } from '../../../shared/utils/apiErrors';

interface RegisterPageProps {
  onNavigate: (route: Route) => void;
  onRegister: (user: AuthUser, accessToken?: string) => void;
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
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange =
    (field: 'fullName' | 'email' | 'password' | 'confirmPassword') =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
    };

  // Previzualizare locală; imaginea nu este trimisă către server.
  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      setForm((prev) => ({ ...prev, avatarPreview: reader.result as string }));
    };
    reader.readAsDataURL(file);
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
        session.access_token
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
    <div className="flex w-full max-w-full flex-col items-center justify-center gap-8 md:flex-row-reverse md:gap-16">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm text-center md:text-right"
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
          {t('auth.register.eyebrow')}
        </p>
        <h1 className="mb-3 text-3xl font-semibold tracking-tight text-zinc-50 md:text-4xl">
          {t('auth.register.heroTitle')} <span className="text-accent">VitaBalance</span>
        </h1>
        <p className="text-base leading-relaxed text-zinc-400 md:text-sm">{t('auth.register.heroText')}</p>
      </motion.div>

      <GlassCard className="w-full max-w-full md:max-w-md">
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
                <motion.img
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  src={form.avatarPreview}
                  alt={t('auth.register.avatarAlt')}
                  className="h-12 w-12 rounded-full border border-line-strong object-cover"
                />
              )}
            </div>
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
    </div>
  );
};

export default RegisterPage;
