import React, { useState } from 'react';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import { motion } from 'framer-motion';
import type { AuthUser } from '../../../shared/types';

interface LoginPageProps {
  onNavigate: (page: 'register' | 'login') => void;
  onLogin: (user: AuthUser) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onNavigate, onLogin }) => {
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  const handleChange = (field: 'email' | 'password') => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { email?: string; password?: string } = {};
    if (!form.email) newErrors.email = 'Introdu adresa de email.';
    if (!form.password) newErrors.password = 'Introdu parola.';
    setErrors(newErrors);
    
    if (Object.keys(newErrors).length === 0) {
      // Mock login: trimitem un user fake
      onLogin({
        fullName: 'User Demo',
        email: form.email,
        bio: 'Explorator al echilibrului digital și fizic.',
        avatarUrl: null,
      });
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

        <form onSubmit={handleSubmit}>
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

