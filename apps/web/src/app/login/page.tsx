'use client';
import { useT } from '@/lib/i18n/context';
import { LoginForm } from '@/features/auth';
import { AuthShell } from '@/components/auth/auth-shell';

export default function LoginPage() {
  const { t } = useT();

  return (
    <AuthShell title={t("login.title")} subtitle={t("login.subtitle")}>
      <LoginForm />
    </AuthShell>
  );
}
