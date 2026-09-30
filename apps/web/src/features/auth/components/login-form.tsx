'use client';
import { useT } from '@/lib/i18n/context';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { useLogin } from '../hooks/use-login';
import { authApi } from '../api';
import { tokenStore } from '@/lib/auth/token-store';
import { AuthButton, AuthInput, AuthLink } from '@/components/auth/auth-shell';
import { PasswordInput } from '@/components/auth/password-input';

export function LoginForm() {
  const { t } = useT();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [twoFactorToken, setTwoFactorToken] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const login = useLogin();

  const complete2fa = useMutation({
    mutationFn: (payload: { token: string; code: string }) =>
      authApi.twoFactorLogin(payload.token, payload.code),
    onSuccess: (response) => {
      if (response.requires2fa) {
        setErr('Neočakávaný stav. Skús znova.');
        return;
      }
      if (response.accessToken && response.refreshToken) {
        tokenStore.setTokens(response.accessToken, response.refreshToken, true);
        router.push('/dashboard');
      } else {
        setErr('Chýbajú tokeny v odpovedi.');
      }
    },
    onError: () => {
      setErr('Nesprávny alebo expirovaný kód.');
    },
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      const response = await login.mutateAsync({ email, password });
      if (response.requires2fa && response.twoFactorToken) {
        setTwoFactorToken(response.twoFactorToken);
        return;
      }
      router.push('/dashboard');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Prihlásenie zlyhalo';
      setErr(msg);
    }
  };

  const onSubmit2fa = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (!twoFactorToken) {
      setErr('Chýba 2FA token. Skús znova.');
      return;
    }
    await complete2fa.mutateAsync({ token: twoFactorToken, code });
  };

  // ─────────────────────────────────────────────
  // KROK 2: 2FA kod
  // ─────────────────────────────────────────────
  if (twoFactorToken) {
    return (
      <form onSubmit={onSubmit2fa} className="grid gap-3">
        <p className="text-sm" style={{ color: '#e8d48b' }}>
          Zadaj 6-ciferný kód z aplikácie Google Authenticator (alebo backup kód).
        </p>
        <AuthInput
          type="text"
          required
          placeholder="123456 alebo XXXX-XXXX"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          autoComplete="one-time-code"
          inputMode="text"
          maxLength={16}
          autoFocus
        />
        {err ? <p className="text-sm text-[#c45c4a]">{err}</p> : null}
        <AuthButton type="submit" disabled={complete2fa.isPending}>
          {complete2fa.isPending ? 'Overujem…' : 'Pokračovať'}
        </AuthButton>
        <button
          type="button"
          className="text-xs underline"
          style={{ color: '#9a8f7c' }}
          onClick={() => {
            setTwoFactorToken(null);
            setCode('');
            setErr(null);
          }}
        >
          ← Späť na prihlásenie
        </button>
      </form>
    );
  }

  // ─────────────────────────────────────────────
  // KROK 1: email + heslo
  // ─────────────────────────────────────────────
  return (
    <form onSubmit={onSubmit} className="grid gap-3">
      <AuthInput
        type="email"
        required
        placeholder={t('login.email')}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
      />
      <PasswordInput
        value={password}
        onChange={setPassword}
        placeholder={t('login.password')}
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
