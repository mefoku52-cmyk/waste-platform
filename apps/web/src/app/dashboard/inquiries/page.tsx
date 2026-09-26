'use client';

import { AppShell } from '@/components/layout/app-shell';
import { InquiriesTable } from '@/features/inquiries/components/inquiries-table';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';

const BOX_STYLE = {
  borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)',
  background: 'linear-gradient(135deg, rgba(201,168,76,0.06) 0%, rgba(9,8,7,0) 60%)',
};

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

        <section className="mt-8">
          <div className="rounded-2xl border p-5 sm:p-6" style={BOX_STYLE}>
            <div className="mb-4 flex items-baseline gap-3">
              <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>
                {t('inquiries.received')}
              </h2>
              <span className="h-1 w-1 rounded-full" style={{ background: GOLD }} />
            </div>
            <InquiriesTable mode="received" />
          </div>
        </section>

        <section className="mt-6">
          <div className="rounded-2xl border p-5 sm:p-6" style={BOX_STYLE}>
            <div className="mb-4 flex items-baseline gap-3">
              <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>
                {t('inquiries.sent')}
              </h2>
              <span className="h-1 w-1 rounded-full" style={{ background: GOLD }} />
            </div>
            <InquiriesTable mode="sent" />
          </div>
        </section>
      </div>
    </AppShell>
  );
}
