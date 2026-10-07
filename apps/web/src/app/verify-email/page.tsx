'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AuthShell, AuthButton } from '@/components/auth/auth-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

type Status = 'verifying' | 'success' | 'error';

function VerifyEmailContent() {
  const { t } = useT();  // noqa TS6133
  const params = useSearchParams();
  const token = params?.get('token') || '';
  const [status, setStatus] = useState<Status>('verifying');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage(t('verify.missingToken'));
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${config.apiBaseUrl}/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          setStatus('error');
          setMessage(data.message || data.detail || t('verify.failed'));
          return;
        }
        setStatus('success');
        setMessage(data.message || t('verify.success'));
      } catch {
        setStatus('error');
        setMessage(t('verify.connection'));
      }
    })();
  }, [token]);

  return (
    <AuthShell
      title={
        status === 'verifying'
          ? t('verify.verifying')
          : status === 'success'
            ? t('verify.verified')
            : t('verify.titleError')
      }
      subtitle={
        status === 'verifying'
          ? t('verify.subVerifying')
          : status === 'success'
            ? t('verify.subSuccess')
            : t('verify.subError')
      }
    >
      <div className="space-y-5 text-center">
        <p
          className="text-sm leading-relaxed"
          style={{
            color:
              status === 'success'
                ? '#e8d48b'
                : status === 'error'
                  ? '#c45c4a'
                  : '#9a8f7c',
          }}
        >
          {message}
        </p>

        {status === 'success' && (
          <Link href="/login" className="block">
            <AuthButton type="button">{t('auth.goToLogin')}</AuthButton>
          </Link>
        )}

        {status === 'error' && (
          <div className="grid gap-2">
            <Link href="/verify-email-sent" className="block">
              <AuthButton type="button">{t('auth.requestNewLink')}</AuthButton>
            </Link>
            <Link
              href="/login"
              className="block text-xs text-[#9a8f7c] hover:text-[#e8d48b] underline underline-offset-4"
            >
              {t('verify.backToLogin')}
            </Link>
          </div>
        )}
      </div>
    </AuthShell>
  );
}

export default function VerifyEmailPage() {
  // const { t } = useT();
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#090807]" />}>
      <VerifyEmailContent />
    </Suspense>
  );
}
