'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';

import { AppShell } from '@/components/layout/app-shell';
import { useT } from '@/lib/i18n/context';
import { CompanyPageEditor } from '@/features/company-pages/components/company-page-editor';

const GOLD_BRIGHT = '#e8d48b';

export default function CompanyPublicPageEditor() {
  const params = useParams<{ id: string }>();
  const companyId = String(params?.id || '');
  const { t } = useT();

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

        <CompanyPageEditor companyId={companyId} />
      </div>
    </AppShell>
  );
}
