'use client';

import { AppShell } from '@/components/layout/app-shell';
import { InquiriesTable } from '@/features/inquiries/components/inquiries-table';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';

export default function InquiriesPage() {
  const { t } = useT();

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
          {t('inquiries.section')}
        </p>
        <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
          {t('inquiries.title')}
        </h1>

        <section className="mt-7">
          <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('inquiries.received')}</h2>
          <div className="mt-4 overflow-x-auto">
            <InquiriesTable mode="received" />
          </div>
        </section>

        <section className="mt-10">
          <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('inquiries.sent')}</h2>
          <div className="mt-4 overflow-x-auto">
            <InquiriesTable mode="sent" />
          </div>
        </section>
      </div>
    </AppShell>
  );
}
