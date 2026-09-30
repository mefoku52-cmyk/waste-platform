'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { authApi } from '@/features/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useT } from "@/lib/i18n/context";

function ResetForm() {
  const { t } = useT();
  const sp = useSearchParams();
  const router = useRouter();
  const [token, setToken] = useState(sp.get('token') || '');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const res: any = await authApi.resetPassword(token, password);
      setMsg(res.message || 'Heslo zmenené.');
      setTimeout(() => router.push('/login'), 1200);
    } catch (e: any) {
      setErr(e?.message || 'Obnova zlyhala.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow-md">
      <h1 className="text-xl font-bold text-center">{t('reset.newPassword')}</h1>
      <Input placeholder={t('auth.tokenLabel')} value={token} onChange={(e) => setToken(e.target.value)} required />
      <Input type="password" placeholder={t('auth.newPasswordLabel')} value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
      {msg && <div className="rounded bg-green-50 p-2 text-sm text-green-800">{msg}</div>}
      {err && <div className="rounded bg-red-50 p-2 text-sm text-red-700">{err}</div>}
      <Button type="submit" className="w-full" disabled={busy}>{busy ? 'Ukladám...' : 'Zmeniť heslo'}</Button>
      <p className="text-center text-sm"><Link href="/login" className="text-blue-600">{t('auth.backToLogin')}</Link></p>
    </form>
  );
}

export default function ResetPasswordPage() {
  const { t } = useT();
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <Suspense fallback={<div>{t('common.loadingShort')}</div>}>
        <ResetForm />
      </Suspense>
    </div>
  );
}
