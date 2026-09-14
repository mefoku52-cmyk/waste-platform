"use client";

import { LoginForm } from "@/features/auth";
import { useT } from "@/lib/i18n/context";
import { LanguageSwitcher } from "@/components/language-switcher";
import { BrandLogo } from "@/components/brand/logo";

export default function LoginPage() {
  const { t } = useT();
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="absolute right-4 top-4 z-50">
        <LanguageSwitcher />
      </div>
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <BrandLogo size="lg" />
        <p className="max-w-xs text-sm text-slate-600">
          {t('login.platformSubtitle')}
        </p>
      </div>
      <LoginForm />
      <p className="mt-8 text-center text-[11px] text-slate-400">
        Circular Materials Exchange Platform
      </p>
    </div>
  );
}
