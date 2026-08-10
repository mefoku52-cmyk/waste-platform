'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useCurrentUser } from '../hooks/use-current-user';

interface AuthBootstrapProps {
  children: ReactNode;
}

export const AuthBootstrap = ({ children }: AuthBootstrapProps) => {
  const [mounted, setMounted] = useState(false);
  const { isLoading } = useCurrentUser();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Na serveri a pred mountom vždy rovnaký výstup → žiadna hydration chyba
  if (!mounted || isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
};
