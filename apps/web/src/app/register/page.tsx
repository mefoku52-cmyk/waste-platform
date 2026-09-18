'use client';
import { RegisterForm } from '@/features/auth';
import { AuthShell } from '@/components/auth/auth-shell';

export default function RegisterPage() {
  return (
    <AuthShell title="Založte si účet" subtitle="Burza, ktorá dýcha.">
      <RegisterForm />
    </AuthShell>
  );
}
