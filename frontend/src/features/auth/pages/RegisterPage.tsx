import React, { useState, ChangeEvent } from 'react';
import { GlassCard, InputField, PrimaryButton } from '../../../shared/components';
import { motion } from 'framer-motion';
import type { AuthUser } from '../../../shared/types';

interface RegisterPageProps {
  onNavigate: (page: 'login' | 'register') => void;
  onRegister: (user: AuthUser, accessToken?: string) => void;
}

const RegisterPage: React.FC<RegisterPageProps> = ({ onNavigate, onRegister }) => {
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    avatarFile: null as File | null,
    avatarPreview: null as string | null,
  });
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const handleChange =
    (field: 'fullName' | 'email' | 'password' | 'confirmPassword') =>
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
    };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      setForm((prev) => ({
        ...prev,
        avatarFile: file,
        avatarPreview: reader.result as string,
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: {
      fullName?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};
    
    if (!form.fullName) newErrors.fullName = 'Completează numele complet.';
    if (!form.email) newErrors.email = 'Introdu email-ul.';
    if (!form.password || form.password.length < 6)
      newErrors.password = 'Parola trebuie să aibă minim 6 caractere.';
    if (form.password !== form.confirmPassword)
      newErrors.confirmPassword = 'Parolele nu coincid.';
    
    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      try {
        // Apel API pentru register
        const apiUrl = import.meta.env.VITE_API_URL || '/api';
        const response = await fetch(`${apiUrl}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: form.email.trim(),
            password: form.password,
            fullName: form.fullName.trim(),
            bio: 'Spune lumii cine ești.',
          }),
        });

        if (!response.ok) {
          let errorMessage = 'Eroare la crearea contului';
          try {
            const text = await response.text();
            try {
              const errorData = JSON.parse(text);
              const detail = errorData.detail || errorData.message;
              if (typeof detail === 'string') {
                errorMessage = detail;
              } else if (Array.isArray(detail)) {
                errorMessage = detail.map((e: any) => {
                  const msg = e.msg || JSON.stringify(e);
                  const loc = e.loc ? e.loc.join('.') : '';
                  return loc ? `${loc}: ${msg}` : msg;
                }).join('; ');
              } else if (detail && typeof detail === 'object') {
                errorMessage = detail.msg || detail.message || JSON.stringify(detail);
              }
            } catch {
              // Răspunsul nu e JSON (ex.: pagină de eroare) – afișăm primele 200 caractere
              if (text && text.length > 0) {
                errorMessage = text.length > 200 ? text.slice(0, 200) + '…' : text;
              } else {
                errorMessage = `Eroare server (${response.status}). Verifică că backend-ul rulează pe portul 8000.`;
              }
            }
            // Identifică tipul de eroare și setează eroarea corespunzătoare
            const lowerMessage = errorMessage.toLowerCase();
            if (lowerMessage.includes('email') || lowerMessage.includes('deja înregistrat')) {
              setErrors({ email: errorMessage });
            } else if (lowerMessage.includes('parolă') || lowerMessage.includes('password') || lowerMessage.includes('parola')) {
              setErrors({ password: errorMessage });
            } else {
              setErrors({ email: errorMessage });
            }
          } catch (parseError) {
            setErrors({ email: `${errorMessage} (${response.status})` });
          }
          return;
        }

        const user = await response.json();
        onRegister(
          {
            fullName: user.fullName,
            email: user.email,
            bio: user.bio,
            avatarUrl: null,
          },
          user.access_token
        );
      } catch (error: any) {
        console.error('Eroare la înregistrare:', error);
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
        setErrors({ email: errorMessage });
      }
    }
  };

  return (
    <div className="flex w-full flex-col items-center justify-center gap-6 md:flex-row-reverse">
      {/* Text lateral */}
      <motion.div
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-sm"
      >
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-neonMagenta">
          Creează-ți spațiul
        </p>
        <h2 className="mb-3 text-3xl font-semibold tracking-tight sm:text-4xl">
          Cont nou <span className="text-neonMagenta">VitaBalance</span>
        </h2>
        <p className="text-sm text-slate-300">
          Personalizează-ți profilul cu un avatar, bio și date de contact,
          toate într-un ambient neon futurist.
        </p>
      </motion.div>

      {/* Card register */}
      <GlassCard>
        <div className="mb-6">
          <h3 className="text-xl font-semibold tracking-tight text-slate-100">
            Creare cont
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Completează informațiile de mai jos.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <InputField
            label="Nume complet"
            value={form.fullName}
            onChange={handleChange('fullName')}
            placeholder="Nume Prenume"
            error={errors.fullName}
          />
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
          <InputField
            label="Confirmare parolă"
            type="password"
            value={form.confirmPassword}
            onChange={handleChange('confirmPassword')}
            placeholder="Repetă parola"
            error={errors.confirmPassword}
          />

          {/* Upload avatar */}
          <div className="mb-4">
            <label className="mb-1.5 block text-xs font-medium uppercase tracking-[0.16em] text-slate-300">
              Poză de profil
            </label>
            <div className="flex items-center gap-4">
              <label className="inline-flex cursor-pointer items-center rounded-xl border border-dashed border-slate-500/70 bg-black/20 px-3 py-2 text-xs text-slate-200 hover:border-neonCyan hover:text-neonCyan transition">
                <span className="mr-2 text-lg">📁</span>
                <span>Alege o imagine</span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
              </label>
              {form.avatarPreview && (
                <motion.img
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  src={form.avatarPreview}
                  alt="Avatar preview"
                  className="h-12 w-12 rounded-full border border-white/20 object-cover shadow-neon"
                />
              )}
            </div>
          </div>

          <div className="mt-4">
            <PrimaryButton type="submit">Înregistrare</PrimaryButton>
          </div>
        </form>

        <div className="mt-5 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            Ai deja cont?
          </span>
          <button
            onClick={() => onNavigate('login')}
            className="font-semibold text-neonCyan hover:text-neonMagenta transition"
          >
            Înapoi la logare
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default RegisterPage;

