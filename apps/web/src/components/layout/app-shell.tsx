'use client';

import { ReactNode } from 'react';

import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DashboardHeader } from '@/components/layout/dashboard-header';

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="cmep-page">
      <DashboardHeader />
      <main className="cmep-main">{children}</main>
      <DashboardFooter />
    </div>
  );
}
