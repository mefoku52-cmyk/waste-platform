'use client';

import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { useCompanies } from './use-companies';

export type MyTier = 'admin' | 'free' | 'pro' | 'ai' | 'unknown';

type Result = {
  tier: MyTier;
  isLoading: boolean;
  companyId?: string;
};

export const useMyTier = (): Result => {
  const { data: me, isLoading: meLoading } = useCurrentUser();
  const { data: companiesResp, isLoading: companiesLoading } = useCompanies();

  if (meLoading || companiesLoading) return { tier: 'unknown', isLoading: true, companyId: undefined };
  if (!me) return { tier: 'unknown', isLoading: false, companyId: undefined };
  if ((me as any).isPlatformAdmin) return { tier: 'admin', isLoading: false, companyId: undefined };

  const memberships = (me as any).memberships || [];
  if (!memberships.length) return { tier: 'unknown', isLoading: false, companyId: undefined };

  const myCompanyIds = memberships
    .map((m: any) => String(m?.companyId || m?.company_id || ''))
    .filter(Boolean);

  const items = (companiesResp as any)?.items ?? [];
  const myCompany = items.find((c: any) =>
    myCompanyIds.includes(String(c?.id || '')),
  );

  if (!myCompany) return { tier: 'unknown', isLoading: false, companyId: undefined };

  const raw = String(myCompany.subscriptionTier ?? 'free').toLowerCase().trim();
  const cid = String(myCompany.id || '');
  if (raw === 'pro' || raw === 'ai') return { tier: raw, isLoading: false, companyId: cid };
  return { tier: 'free', isLoading: false, companyId: cid };
};
