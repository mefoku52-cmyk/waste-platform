'use client';
import { useT } from '@/lib/i18n/context';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useRegister } from '../hooks/use-register';
import { AuthButton, AuthInput, AuthLink } from '@/components/auth/auth-shell';
import { PasswordInput } from '@/components/auth/password-input';
import { TurnstileWidget } from '@/components/auth/turnstile-widget';

export function RegisterForm() {
  const { t } = useT();
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [turnstileToken, setTurnstileToken] = useState<string>('');
  const register = useRegister();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      await register.mutateAsync({ email, password, name, turnstileToken });
      router.push('/verify-email-sent?email=' + encodeURIComponent(email));
    } catch (e: unknown) {
      const msg =
        e instanceof Error
          ? e.message
          : typeof e === 'object' && e && 'message' in e
            ? String((e as { message: unknown }).message)
            : t('register.submit') + ' failed';
      setErr(msg);
    }
  };

  return (
    <form onSubmit={onSubmit} className="grid gap-3">
      <AuthInput
        placeholder={t('register.name')}
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoComplete="name"
      />
      <AuthInput
        type="email"
        required
        placeholder={t('register.email')}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoComplete="email"
      />
      <PasswordInput
        value={password}
        onChange={setPassword}
        required
        minLength={8}
        autoComplete="new-password"
        placeholder={t('register.password')}
      />
      <TurnstileWidget onVerify={setTurnstileToken} onExpire={() => setTurnstileToken('')} />
      {err ? <p className="text-sm text-[#c45c4a]">{err}</p> : null}
      <AuthButton type="submit" disabled={register.isPending}>
        {register.isPending ? t('register.submit') + '…' : t('register.submit')}
      </AuthButton>
      <AuthLink href="/login">{t('register.login')}</AuthLink>
    </form>
  );
}
