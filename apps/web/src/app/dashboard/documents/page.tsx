'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { useDocuments } from '@/features/documents';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';

export default function DocumentsPage() {
  const { t } = useT();
  const query = useDocuments() as { data?: unknown; isLoading?: boolean };
  const raw = query.data as { data?: unknown[]; items?: unknown[] } | unknown[] | undefined;
  const items = Array.isArray(raw) ? raw : raw?.data ?? raw?.items ?? [];

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-5xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em]" style={{ color: GOLD }}>
              {t('documents.section')}
            </p>
            <h1 className="mt-2 font-serif text-3xl sm:text-4xl" style={{ color: GOLD_BRIGHT }}>
              {t('documents.title')}
            </h1>
          </div>
          <Link href="/dashboard/documents/new" className="rounded-full border px-4 py-2 text-sm" style={{ borderColor: 'rgba(201,168,76,0.48)', color: GOLD_BRIGHT }}>
            + {t('documents.addButton')}
          </Link>
        </div>

        {query.isLoading ? (
          <p className="text-sm" style={{ color: MUTED }}>{t('common.loading')}</p>
        ) : items.length === 0 ? (
          <section className="cmep-panel rounded-2xl px-5 py-14 text-center">
            <h2 className="font-serif text-2xl" style={{ color: GOLD_BRIGHT }}>{t('documents.empty')}</h2>
            <p className="mt-2 text-sm" style={{ color: MUTED }}>{t('documents.emptyHint')}</p>
          </section>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {(items as Array<Record<string, unknown>>).map((document, index) => (
              <li key={String(document.id || document.title || `document-${index}`)} className="cmep-card rounded-2xl p-5">
                <p className="font-serif text-xl" style={{ color: GOLD_BRIGHT }}>
                  {String(document.title || document.name || t('documents.docTitle'))}
                </p>
                <p className="mt-2 text-sm" style={{ color: MUTED }}>
                  {String(document.document_type || document.documentType || '—')}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}
