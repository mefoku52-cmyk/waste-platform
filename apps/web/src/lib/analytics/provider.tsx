'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

import { captureFirstTouch, track } from './track';

const SESSION_FLAG = 'cmep_session_started';

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const bootstrapped = useRef(false);

  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;

    captureFirstTouch();
    if (!sessionStorage.getItem(SESSION_FLAG)) {
      sessionStorage.setItem(SESSION_FLAG, '1');
      void track('landing_view');
    }
  }, []);

  useEffect(() => {
    if (!pathname) return;
    void track('page_view');
  }, [pathname]);

  return <>{children}</>;
}
