'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useT } from '@/lib/i18n/context';

function ChatDraftBannerInner() {
  const { t } = useT();
  const params = useSearchParams();
  const draft = params.get('draft') || '';
  if (!draft) return null;
  return (
    <div className="mb-4 rounded-2xl border border-[#d4af37]/35 bg-black p-4 text-[#f3e6c4]">
      <p className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37]">{t('chatDraftBanner.kicker')}</p>
      <p className="mt-2 whitespace-pre-wrap text-sm text-[#cbb98a]">{draft}</p>
      <button
        type="button"
        className="mt-3 rounded-full border border-[#d4af37]/50 px-3 py-1 text-xs text-[#d4af37]"
        onClick={() => navigator.clipboard.writeText(draft)}
      >
        Kopirovat do spravy
      </button>
    </div>
  );
}

export function ChatDraftBanner() {
  return (
    <Suspense fallback={null}>
      <ChatDraftBannerInner />
    </Suspense>
  );
}
