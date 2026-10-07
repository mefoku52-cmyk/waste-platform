'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AuthShell, AuthButton, AuthInput } from '@/components/auth/auth-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

function VerifyEmailSentContent() {
  const { t } = useT();  // noqa TS6133 - t is used in inner scope
  const params = useSearchParams();
  const initialEmail = params?.get('email') || '';
  const [email, setEmail] = useState(initialEmail);
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const onResend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('sending');
    setError(null);
    try {
      const res = await fetch(`${config.apiBaseUrl}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.detail || t('verifySent.sendError'));
      }
      setStatus('sent');
    } catch (e: unknown) {
      setStatus('error');
      setError(e instanceof Error ? e.message : t('verifySent.sendError'));
    }
  };

  return (
    <AuthShell
      title={t('auth.sentTitle')}
      subtitle={t('auth.sentSubtitle')}
    >
      <div className="space-y-5 text-[#9a8f7c]">
        <p className="text-sm leading-relaxed">
          {t('verifySent.sentTo')}{' '}
          <strong className="text-[#e8d48b]">{email || '—'}</strong>{' '}
          {t('verifySent.sentDesc')}
        </p>
        <p className="text-xs leading-relaxed">
          {t('verifySent.spamHint')} <strong>{t('auth.sentSpamBold')}</strong> alebo{' '}
          <strong>{t('auth.sentPromotions')}</strong>. Odkaz je platný 24 hodín.
        </p>

        <div className="pt-3 border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <p className="mb-3 text-xs uppercase tracking-[0.2em] text-[#c9a84c]">
            {t('verifySent.noEmail')}
          </p>

          {status === 'sent' ? (
            <p className="text-sm text-[#e8d48b]">
              {t('verifySent.resentOk')}
            </p>
          ) : (
            <form onSubmit={onResend} className="grid gap-3">
              <AuthInput
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('auth.emailLabel')}
              />
              {error && <p className="text-sm text-[#c45c4a]">{error}</p>}
              <AuthButton type="submit" disabled={status === 'sending'}>
                {status === 'sending' ? t('verifySent.sending') : t('verifySent.resendBtn')}
              </AuthButton>
            </form>
          )}
        </div>

        <div className="text-center text-xs">
          <Link href="/login" className="text-[#9a8f7c] hover:text-[#e8d48b] underline underline-offset-4">
            {t('verifySent.backToLogin')}
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}

export default function VerifyEmailSentPage() {
  // const { t } = useT();
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#090807]" />}>
      <VerifyEmailSentContent />
    </Suspense>
  );
}
