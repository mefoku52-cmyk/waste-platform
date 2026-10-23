'use client';

import { ReactNode } from 'react';
import { redirect } from 'next/navigation';

import { useAuthRequired, useIsPlatformAdmin } from '@/features/auth';

/**
 * Admin UI guard. Backend endpoints sú autoritatívne (require_admin); toto je
 * len vrstva, ktorá nedovolí vykresliť admin stránky tenant administrátorovi.
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  const { isLoading } = useAuthRequired();
  const isPlatformAdmin = useIsPlatformAdmin();

  if (isLoading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{ background: '#090807' }}
      >
        <div className="text-sm" style={{ color: '#9a8f7c' }}>
          Načítavam…
        </div>
      </div>
    );
  }

  if (!isPlatformAdmin) {
    redirect('/dashboard');
  }

  return <>{children}</>;
}
