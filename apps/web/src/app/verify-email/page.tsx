'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AuthShell, AuthButton } from '@/components/auth/auth-shell';
import { config } from '@/lib/config';

type Status = 'verifying' | 'success' | 'error';

function VerifyEmailContent() {
  const params = useSearchParams();
  const token = params?.get('token') || '';
  const [status, setStatus] = useState<Status>('verifying');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('Chýba overovací token v adrese.');
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
          setMessage(data.message || data.detail || 'Overenie zlyhalo.');
          return;
        }
        setStatus('success');
        setMessage(data.message || 'E-mail bol úspešne overený.');
      } catch {
        setStatus('error');
        setMessage('Nepodarilo sa spojiť so serverom.');
      }
    })();
  }, [token]);

  return (
    <AuthShell
      title={
        status === 'verifying'
          ? 'Overujem e-mail…'
          : status === 'success'
            ? 'E-mail overený'
            : 'Overenie zlyhalo'
      }
      subtitle={
        status === 'verifying'
          ? 'Chvíľku strpenia.'
          : status === 'success'
            ? 'Môžete sa prihlásiť.'
            : 'Skúste znova alebo požiadajte o nový odkaz.'
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
            <AuthButton type="button">Prejsť na prihlásenie</AuthButton>
          </Link>
        )}

        {status === 'error' && (
          <div className="grid gap-2">
            <Link href="/verify-email-sent" className="block">
              <AuthButton type="button">Požiadať o nový odkaz</AuthButton>
            </Link>
            <Link
              href="/login"
              className="block text-xs text-[#9a8f7c] hover:text-[#e8d48b] underline underline-offset-4"
            >
              Späť na prihlásenie
            </Link>
          </div>
        )}
      </div>
    </AuthShell>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#090807]" />}>
      <VerifyEmailContent />
    </Suspense>
  );
}
