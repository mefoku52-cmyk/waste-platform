'use client';

import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { useCompanies } from './use-companies';

export type MyTier = 'admin' | 'free' | 'pro' | 'ai' | 'unknown';

type Result = {
  tier: MyTier;
  isLoading: boolean;
};

export const useMyTier = (): Result => {
  const { data: me, isLoading: meLoading } = useCurrentUser();
  const { data: companiesResp, isLoading: companiesLoading } = useCompanies();

  if (meLoading || companiesLoading) return { tier: 'unknown', isLoading: true };
  if (!me) return { tier: 'unknown', isLoading: false };
  if ((me as any).isPlatformAdmin) return { tier: 'admin', isLoading: false };

  const memberships = (me as any).memberships || [];
  if (!memberships.length) return { tier: 'unknown', isLoading: false };

  const myCompanyIds = memberships
    .map((m: any) => String(m?.companyId || m?.company_id || ''))
    .filter(Boolean);

  const items = (companiesResp as any)?.items ?? [];
  const myCompany = items.find((c: any) =>
    myCompanyIds.includes(String(c?.id || '')),
  );

  if (!myCompany) return { tier: 'unknown', isLoading: false };

  const raw = String(myCompany.subscriptionTier ?? 'free').toLowerCase().trim();
  if (raw === 'pro' || raw === 'ai') return { tier: raw, isLoading: false };
  return { tier: 'free', isLoading: false };
};
