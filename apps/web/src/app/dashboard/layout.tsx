'use client';

import { ReactNode } from 'react';

import { useAuthRequired } from '@/features/auth/hooks/use-auth-required';

/**
 * Dashboard layout guard: všetky stránky pod /dashboard vyžadujú prihlásenie.
 * Oprávnenia sa vždy overujú aj na serveri — toto je len UI vrstva, ktorá
 * presmeruje neprihláseného používateľa na /login.
 */
import { AiChatWidget } from '@/features/agent-platform/components/ai-chat-widget';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { isLoading } = useAuthRequired();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: '#090807' }}>
        <div className="text-sm" style={{ color: '#9a8f7c' }}>
          Načítavam…
        </div>
      </div>
    );
  }

  return <>{children}
        <AiChatWidget /></>;
}