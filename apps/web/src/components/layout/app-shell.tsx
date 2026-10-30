'use client';

import { ReactNode } from 'react';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';

import { FeedbackWidget } from '@/features/feedback/components/feedback-widget';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';

export function AppShell({ children }: { children: ReactNode }) {
  const { data: me } = useCurrentUser();
  const isLoggedIn = Boolean(me && (me as any).id);

  return (
    <div className="cmep-page">
      <DashboardHeader />
      <main className="cmep-main">{children}</main>
      <DashboardFooter />
      
      {isLoggedIn ? <FeedbackWidget /> : null}
    </div>
  );
}
