'use client';

import { useState } from 'react';
import Link from 'next/link';
import { authApi } from '@/features/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useT } from "@/lib/i18n/context";

export default function ForgotPasswordPage() {
  const { t } = useT();
  const [email, setEmail] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    setDevToken(null);
    try {
      const res: any = await authApi.forgotPassword(email);
      setMsg(res.message || t('forgot.successMsg'));
      if (res.resetToken) setDevToken(res.resetToken);
    } catch (err: any) {
      setMsg(err?.message || t('forgot.errorMsg'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow-md">
        <h1 className="text-xl font-bold text-center">{t('forgot.title')}</h1>
        <p className="text-sm text-gray-500">{t('forgot.description')}</p>
        <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vas@email.sk" />
        {msg && <div className="rounded bg-blue-50 p-2 text-sm text-blue-800">{msg}</div>}
        {devToken && (
          <div className="rounded bg-amber-50 p-2 text-xs text-amber-900 break-all">
            {t('forgot.devToken')} {devToken}
            <div className="mt-2">
              <Link className="text-blue-600 underline" href={`/reset-password?token=${encodeURIComponent(devToken)}`}>
                {t('forgot.continueLink')}
              </Link>
            </div>
          </div>
        )}
        <Button type="submit" className="w-full" disabled={busy}>{busy ? t('forgot.sending') : t('forgot.send')}</Button>
        <p className="text-center text-sm"><Link href="/login" className="text-blue-600">{t('forgot.back')}</Link></p>
      </form>
    </div>
  );
}
