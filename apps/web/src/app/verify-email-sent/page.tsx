'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { AuthShell, AuthButton, AuthInput } from '@/components/auth/auth-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';

function VerifyEmailSentContent() {
  const { t } = useT();
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
        throw new Error(err.message || err.detail || 'Nepodarilo sa odoslať e-mail.');
      }
      setStatus('sent');
    } catch (e: unknown) {
      setStatus('error');
      setError(e instanceof Error ? e.message : 'Nepodarilo sa odoslať e-mail.');
    }
  };

  return (
    <AuthShell
      title={t('auth.sentTitle')}
      subtitle={t('auth.sentSubtitle')}
    >
      <div className="space-y-5 text-[#9a8f7c]">
        <p className="text-sm leading-relaxed">
          Na adresu{' '}
          <strong className="text-[#e8d48b]">{email || '—'}</strong>{' '}
          sme poslali odkaz na overenie účtu. Kliknite naň a dokončite registráciu.
        </p>
        <p className="text-xs leading-relaxed">
          Ak e-mail nevidíte, skontrolujte priečinok <strong>Spam</strong> alebo{' '}
          <strong>Promócie</strong>. Odkaz je platný 24 hodín.
        </p>

        <div className="pt-3 border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <p className="mb-3 text-xs uppercase tracking-[0.2em] text-[#c9a84c]">
            Nedostali ste e-mail?
          </p>

          {status === 'sent' ? (
            <p className="text-sm text-[#e8d48b]">
              ✓ Poslali sme nový overovací odkaz. Skontrolujte schránku.
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
                {status === 'sending' ? 'Odosielam…' : 'Znova odoslať verifikačný e-mail'}
              </AuthButton>
            </form>
          )}
        </div>

        <div className="text-center text-xs">
          <Link href="/login" className="text-[#9a8f7c] hover:text-[#e8d48b] underline underline-offset-4">
            Späť na prihlásenie
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}

export default function VerifyEmailSentPage() {
  const { t } = useT();
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#090807]" />}>
      <VerifyEmailSentContent />
    </Suspense>
  );
}
