'use client';

import { tokenStore } from '@/lib/auth/token-store';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';

import { AppShell } from '@/components/layout/app-shell';
import { config } from '@/lib/config';
import { useT } from '@/lib/i18n/context';
import { CompanyForm } from '@/features/companies/components/company-form';

const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

type CompanyData = {
  id: string;
  legalName?: string | null;
  tradingName?: string | null;
  registrationNumber?: string | null;
  taxIdentifier?: string | null;
  vatIdentifier?: string | null;
  companyType?: string | null;
  entityType?: string | null;
  email?: string | null;
  phone?: string | null;
  countryCode?: string | null;
  addressLine1?: string | null;
  addressLine2?: string | null;
  city?: string | null;
  postalCode?: string | null;
  sellerCapability?: boolean | null;
  buyerCapability?: boolean | null;
  logisticsCapability?: boolean | null;
};

async function fetchCompany(id: string): Promise<CompanyData> {
  const token = tokenStore.getToken();
  const res = await fetch(`${config.apiBaseUrl}/companies/${id}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`);
  }
  return (body.data ?? body) as CompanyData;
}

export default function CompanyEditPage() {
  const params = useParams<{ id: string }>();
  const companyId = String(params?.id || '');
  const { t } = useT();

  const query = useQuery({
    queryKey: ['company', companyId],
    queryFn: () => fetchCompany(companyId),
    enabled: Boolean(companyId),
    retry: 1,
  });

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-4xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <Link
          href={`/dashboard/companies/${companyId}`}
          className="inline-flex rounded-full border px-3 py-1.5 text-sm"
          style={{ borderColor: 'rgba(201,168,76,0.38)', color: GOLD_BRIGHT }}
        >
          ← {t('common.back')}
        </Link>

        {query.isLoading ? (
          <p className="mt-8 text-sm" style={{ color: MUTED }}>{t('companies.contactsLoading')}</p>
        ) : query.error ? (
          <div className="mt-8 rounded-2xl border border-[#c45c4a]/60 bg-[#c45c4a]/10 p-4 text-sm text-[#f0bbb0]">
            {query.error instanceof Error ? query.error.message : t('companies.loadError')}
          </div>
        ) : query.data ? (
          <div className="mt-6">
            <CompanyForm
              mode="edit"
              companyId={companyId}
              initialData={query.data as any}
            />
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
