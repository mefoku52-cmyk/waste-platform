'use client';
import { LoginForm } from '@/features/auth';
import { AuthShell } from '@/components/auth/auth-shell';

export default function LoginPage() {
  return (
    <AuthShell title="Vstup na burzu" subtitle="E-mailom. Žiadny zelený lístok.">
      <LoginForm />
    </AuthShell>
  );
}
