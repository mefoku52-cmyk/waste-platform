'use client';

import { ReactNode } from 'react';
import { useCurrentUser } from '../hooks/use-current-user';

interface AuthBootstrapProps {
  children: ReactNode;
}

/**
 * AuthBootstrap — prednačíta aktuálneho používateľa, ale NIKDY neblokuje render.
 *
 * Predtým na serveri (mounted=false) aj počas načítavania vracal spinner namiesto
 * children. To spôsobovalo, že sa celý strom odosielal ako streamovaný "shell":
 * HTTP stav sa zamkol na 200 (takže notFound() na /firma/* robil soft-404) a obsah
 * stránok sa reálne neserver-renderoval (crawler/social videli len spinner).
 *
 * Ochrana chránených stránok je v app/dashboard/layout.tsx (useAuthRequired)
 * a autoritatívne na serveri — preto tento komponent len renderuje children.
 */
export const AuthBootstrap = ({ children }: AuthBootstrapProps) => {
  // Teplý štart: prednačíta /me, ale nezablokuje serverový ani klientsky render.
  useCurrentUser();

  return <>{children}</>;
};
