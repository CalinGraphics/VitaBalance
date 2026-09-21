import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import type { AuthUser, Route } from '../../../shared/types';
import { authService } from '../../../services/api';
import { extractErrorMessage } from '../../../shared/utils/apiErrors';

interface LoginPageProps {
  onNavigate: (route: Route) => void;
  onLogin: (user: AuthUser, accessToken?: string) => void;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const LoginPage: React.FC<LoginPageProps> = ({ onNavigate, onLogin }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = t('apiErrors.emailRequired');
    else if (!EMAIL_PATTERN.test(email.trim())) errors.email = t('apiErrors.invalidEmail');
    if (!password) errors.password = t('apiErrors.passwordRequired');
    setFieldErrors(errors);
    setFormError(null);
    if (Object.keys(errors).length > 0) return;

    setIsLoading(true);
    try {
      const session = await authService.login(email, password);
      onLogin(
        { email: session.email, fullName: session.fullName, avatarUrl: null },
        session.access_token
      );
    } catch (err: unknown) {
      setFormError(extractErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full max-w-full flex-col items-center justify-center gap-8 md:flex-row md:gap-16">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm text-center md:text-left"
      >
        <h1 className="mb-3 text-3xl font-semibold tracking-tight text-zinc-50 md:text-4xl">
          {t('auth.login.heroTitle')} <span className="text-accent">VitaBalance</span>
        </h1>
        <p className="text-base leading-relaxed text-zinc-400 md:text-sm">{t('auth.login.heroText')}</p>
      </motion.div>

      <GlassCard className="w-full max-w-full md:max-w-md">
        <div className="mb-6">
          <h2 className="text-xl font-semibold tracking-tight text-zinc-50">{t('auth.login.cardTitle')}</h2>
          <p className="mt-1 text-sm leading-relaxed text-zinc-400">{t('auth.login.cardSubtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <InputField
            label={t('auth.fields.email')}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('auth.fields.emailPlaceholder')}
            error={fieldErrors.email}
            autoComplete="email"
            inputMode="email"
          />
          <InputField
            label={t('auth.fields.password')}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('auth.fields.passwordPlaceholder')}
            error={fieldErrors.password}
            autoComplete="current-password"
          />

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
              {isLoading ? t('auth.login.submitting') : t('auth.login.submit')}
            </PrimaryButton>
          </div>
        </form>

        <div className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5 text-sm">
          <span className="text-zinc-400">{t('auth.login.noAccount')}</span>
          <button
            type="button"
            onClick={() => onNavigate('register')}
            className="min-h-[44px] cursor-pointer px-1 font-semibold text-accent transition-colors hover:text-accent-hover touch-manipulation"
          >
            {t('auth.login.createAccount')}
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default LoginPage;
