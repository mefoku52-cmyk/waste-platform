'use client';
import { useT } from '@/lib/i18n/context';
import { RegisterForm } from '@/features/auth';
import { AuthShell } from '@/components/auth/auth-shell';

export default function RegisterPage() {
  const { t } = useT();

  return (
    <AuthShell title={t("register.title")} subtitle={t("register.subtitle")}>
      <RegisterForm />
    </AuthShell>
  );
}
