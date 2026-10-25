'use client';

import { ReactNode } from 'react';
import { redirect } from 'next/navigation';

import { useAuthRequired } from '@/features/auth';

/**
 * Admin UI guard. Backend endpoints sú autoritatívne (require_admin); toto je
 * len vrstva, ktorá nedovolí vykresliť admin stránky tenant administrátorovi.
 */
export default function AdminLayout({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuthRequired();


  if (isLoading || !user) {
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

  if (!user.isPlatformAdmin) {
    redirect('/dashboard');
  }

  return (
    <>
      <nav
        aria-label="Administratorske nastroje"
        className="border-b border-[#c9a84c]/20 bg-[#090807] px-4 py-3"
      >
        <a
          href="/dashboard/admin/diagnostics"
          className="text-sm text-[#e8d48b] underline"
        >
          Diagnostika platformy
        </a>
      </nav>
      {children}
    </>
  );
}
