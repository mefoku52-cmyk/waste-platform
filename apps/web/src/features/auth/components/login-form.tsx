'use client';
import { useT } from '@/lib/i18n/context';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLogin } from '../hooks/use-login';
import { AuthButton, AuthInput, AuthLink } from '@/components/auth/auth-shell';
import { PasswordInput } from '@/components/auth/password-input';

export function LoginForm() {
  const { t } = useT();

  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const login = useLogin();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      await login.mutateAsync({ email, password });
      router.push('/dashboard');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Prihlásenie zlyhalo';
      setErr(msg);
    }
  };

  return (
    <form onSubmit={onSubmit} className="grid gap-3">
      <AuthInput
        type="email"
        required
        placeholder={t("login.email")}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
      />
      <PasswordInput
        value={password}
        onChange={setPassword}
        placeholder={t("login.password")}
        required
        minLength={8}
        autoComplete="current-password"
      />
      {err ? <p className="text-sm text-[#c45c4a]">{err}</p> : null}
      <AuthButton type="submit" disabled={login.isPending}>
        {login.isPending ? t('login.pending') : t('login.submit')}
      </AuthButton>
      <AuthLink href="/forgot-password">{t('login.forgot')}</AuthLink>
      <AuthLink href="/register">{t('login.register')}</AuthLink>
    </form>
  );
}
