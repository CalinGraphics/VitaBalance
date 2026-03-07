import React, { useState } from 'react';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import { motion } from 'framer-motion';
import type { AuthUser } from '../../../shared/types';
import { authService } from '../../../services/api';

interface LoginPageProps {
  onNavigate?: (page: 'register' | 'login') => void;
  onLogin?: (user: AuthUser, accessToken?: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = () => {
  const [email, setEmail] = useState('');
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [magicLinkError, setMagicLinkError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email?.trim()) {
      setMagicLinkError('Introdu adresa de email.');
      return;
    }
    setMagicLinkError(null);
    setIsLoading(true);
    try {
      await authService.requestMagicLink(email.trim());
      setMagicLinkSent(true);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setMagicLinkError(e?.message || 'Eroare la trimitere. Încearcă din nou.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex w-full flex-col items-center justify-center gap-6 sm:gap-8 md:flex-row max-w-full">
      {/* Text lateral - stacked on mobile */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-sm text-center md:text-left"
      >
        <p className="mb-2 text-xs sm:text-xs font-semibold uppercase tracking-[0.22em] text-neonCyan">
          Bine ai revenit
        </p>
        <h2 className="mb-3 text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight text-slate-100">
          Bine ai venit la <span className="text-neonCyan">VitaBalance</span>
        </h2>
        <p className="text-base sm:text-sm text-slate-300 leading-relaxed">
          Hrănește-ți echilibrul și lasă-ți energia
          să revină la nivelul ei natural.
        </p>
      </motion.div>

      {/* Card login - full width on mobile */}
      <GlassCard className="w-full max-w-full md:max-w-md">
        <div className="mb-5 sm:mb-6">
          <h3 className="text-lg sm:text-xl font-semibold tracking-tight text-slate-100">
            Autentificare
          </h3>
          <p className="mt-1 text-xs sm:text-xs text-slate-400 leading-relaxed">
            Introdu email-ul și primești un link de conectare. Dacă nu ai cont, îți va fi creat automat la prima utilizare.
          </p>
        </div>

        {magicLinkSent ? (
          <div className="space-y-4">
            <div className="rounded-lg border border-neonCyan/40 bg-neonCyan/10 px-4 py-4">
              <p className="text-sm text-neonCyan font-medium">
                Linkul a fost trimis la {email}
              </p>
              <p className="mt-2 text-xs text-slate-300">
                Verifică inbox-ul (și spam-ul) și apasă pe link. Expiră în 24h. Dacă nu ai cont, acesta va fi creat automat.
              </p>
            </div>
            <button
              type="button"
              onClick={() => { setMagicLinkSent(false); setEmail(''); setMagicLinkError(null); }}
              className="min-h-[44px] inline-flex items-center justify-center px-3 py-2 text-sm text-slate-400 hover:text-neonCyan transition touch-manipulation"
            >
              Trimite din nou la altă adresă
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            <InputField
              label="Email"
              type="email"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
                setEmail(e.target.value)
              }
              placeholder="exemplu@email.com"
              error={magicLinkError ?? undefined}
            />
            <div className="mt-6">
              <PrimaryButton type="submit" disabled={isLoading}>
                <span>{isLoading ? 'Se trimite...' : 'Trimite link de conectare'}</span>
              </PrimaryButton>
            </div>
          </form>
        )}
      </GlassCard>
    </div>
  );
};

export default LoginPage;

