'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useRegister } from '../hooks/use-register';
import { AuthButton, AuthInput, AuthLink } from '@/components/auth/auth-shell';
import { PasswordInput } from '@/components/auth/password-input';

export function RegisterForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const register = useRegister();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    try {
      await register.mutateAsync({ email, password, name } as never);
      // Presmeruj na stranku "Skontrolujte e-mail"
      router.push(`/verify-email-sent?email=${encodeURIComponent(email)}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Registrácia zlyhala';
      setErr(msg);
    }
  };

  return (
    <form onSubmit={onSubmit} className="grid gap-3">
      <AuthInput
        placeholder="Meno"
        value={name}
        onChange={(e) => setName(e.target.value)}
        autoComplete="name"
      />
      <AuthInput
        type="email"
        required
        placeholder="E-mail"
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
        placeholder="Heslo (min. 8 znakov)"
      />
      {err ? <p className="text-sm text-[#c45c4a]">{err}</p> : null}
      <AuthButton type="submit" disabled={register.isPending}>
        {register.isPending ? 'Zakladám…' : 'Založiť účet'}
      </AuthButton>
      <AuthLink href="/login">Už máte účet? Prihláste sa.</AuthLink>
    </form>
  );
}
