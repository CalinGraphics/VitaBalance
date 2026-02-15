import React, { useState } from 'react';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import { motion } from 'framer-motion';
import type { AuthUser } from '../../../shared/types';
import { authService } from '../../../services/api';

interface LoginPageProps {
  onNavigate: (page: 'register' | 'login') => void;
  onLogin: (user: AuthUser, accessToken?: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onNavigate, onLogin }) => {
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [magicLinkError, setMagicLinkError] = useState<string | null>(null);

  const handleChange = (field: 'email' | 'password') => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { email?: string; password?: string } = {};
    if (!form.email) newErrors.email = 'Introdu adresa de email.';
    if (!form.password) newErrors.password = 'Introdu parola.';
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length === 0) {
      try {
        // Apel API pentru login
        const apiUrl = import.meta.env.VITE_API_URL || '/api';
        const response = await fetch(`${apiUrl}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: form.email,
            password: form.password,
          }),
        });

        if (!response.ok) {
          let errorMessage = 'Email sau parolă incorectă';
          try {
            const errorData = await response.json();
            const detail = errorData.detail || errorData.message;
            if (typeof detail === 'string') {
              errorMessage = detail;
            } else if (Array.isArray(detail)) {
              errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
            } else if (detail && typeof detail === 'object') {
              errorMessage = detail.msg || detail.message || JSON.stringify(detail);
            }
          } catch (parseError) {
            // Dacă nu poate parsa JSON-ul, folosește mesajul de eroare generic
            errorMessage = 'Eroare la autentificare. Vă rugăm să încercați din nou.';
          }
          setErrors({ password: errorMessage });
          return;
        }

        const user = await response.json();
        onLogin(
          {
            fullName: user.fullName,
            email: user.email,
            bio: user.bio,
            avatarUrl: null,
          },
          user.access_token
        );
      } catch (error: any) {
        console.error('Eroare la autentificare:', error);
        let errorMessage = 'Eroare la conectare. Vă rugăm să încercați din nou.';
        if (error instanceof Error) {
          errorMessage = error.message;
        } else if (error?.response?.data?.detail) {
          const detail = error.response.data.detail;
          if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (Array.isArray(detail)) {
            errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
          } else if (typeof detail === 'object') {
            errorMessage = detail.msg || detail.message || JSON.stringify(detail);
          }
        }
        setErrors({ password: errorMessage });
      }
    }
  };

  return (
    <div className="flex w-full flex-col items-center justify-center gap-6 md:flex-row">
      {/* Text lateral */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-sm"
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-neonCyan">
          Bine ai revenit
        </p>
        <h2 className="mb-3 text-3xl font-semibold tracking-tight sm:text-4xl">
          Bine ai venit la <span className="text-neonCyan">VitaBalance</span>
        </h2>
        <p className="text-sm text-slate-300">
          Hrănește-ți echilibrul și lasă-ți energia 
          să revină la nivelul ei natural.
        </p>
      </motion.div>

      {/* Card login */}
      <GlassCard>
        <div className="mb-6">
          <h3 className="text-xl font-semibold tracking-tight text-slate-100">
            Logare utilizator
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Introdu datele contului pentru a continua.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <InputField
            label="Email"
            type="email"
            value={form.email}
            onChange={handleChange('email')}
            placeholder="exemplu@email.com"
            error={errors.email}
          />
          <InputField
            label="Parolă"
            type="password"
            value={form.password}
            onChange={handleChange('password')}
            placeholder="••••••••"
            error={errors.password}
          />

          <div className="mt-6">
            <PrimaryButton type="submit">
              <span>Autentificare</span>
            </PrimaryButton>
          </div>
        </form>

        <div className="my-5 flex items-center gap-2 text-xs text-slate-500">
          <span className="flex-1 border-t border-slate-600" />
          <span>sau</span>
          <span className="flex-1 border-t border-slate-600" />
        </div>

        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            Autentificare fără parolă – primești un link pe email.
          </p>
          {magicLinkSent ? (
            <p className="rounded-lg border border-slate-500/50 bg-slate-800/30 px-3 py-3 text-sm text-neonCyan">
              Verifică emailul și apasă pe linkul primit. Linkul expiră în 24h.
            </p>
          ) : (
            <>
              <InputField
                label="Email (pentru link magic)"
                type="email"
                value={form.email}
                onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                placeholder="exemplu@email.com"
                error={magicLinkError ?? undefined}
              />
              <PrimaryButton
                type="button"
                onClick={async () => {
                  if (!form.email?.trim()) {
                    setMagicLinkError('Introdu adresa de email.');
                    return;
                  }
                  setMagicLinkError(null);
                  try {
                    await authService.requestMagicLink(form.email.trim());
                    setMagicLinkSent(true);
                  } catch (e: any) {
                    setMagicLinkError(e?.message || 'Eroare la trimitere.');
                  }
                }}
              >
                <span>Trimite link magic</span>
              </PrimaryButton>
            </>
          )}
        </div>

        <div className="mt-5 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            Nu ai cont?
          </span>
          <button
            onClick={() => onNavigate('register')}
            className="font-semibold text-neonCyan hover:text-neonMagenta transition"
          >
            Creează un cont nou
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default LoginPage;

