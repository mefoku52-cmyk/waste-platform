'use client';

import { useState } from 'react';
import { inquiriesApi } from '../api';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';
import { useT } from '@/lib/i18n/context';

export function ListingInquiryButton({
  listingId,
  listingTitle,
}: {
  listingId: string;
  listingTitle?: string;
}) {
  const { t } = useT();
  const me = useCurrentUser();
  const [pending, setPending] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const companyId = me.data?.memberships?.[0]?.companyId;
  const email = me.data?.email || '';

  const send = async () => {
    if (!companyId) {
      setMsg(t('listingInquiry.noCompany'));
      return;
    }
    setPending(true);
    setMsg(null);
    try {
      await inquiriesApi.create({
        listingId,
        companyId,
        contactEmail: email,
        message: 'Dopyt k ponuke ' + (listingTitle || listingId) + '.',
      });
      setMsg(t('listingInquiry.sentOk'));
    } catch (e: unknown) {
      const text =
        e instanceof Error
          ? e.message
          : typeof e === 'object' && e && 'message' in e
            ? String((e as { message: unknown }).message)
            : 'Dopyt zlyhal';
      setMsg(t('listingInquiry.error'));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="mt-4">
      <button
        type="button"
        disabled={pending}
        onClick={() => void send()}
        className="rounded-full border border-[#d4af37]/50 px-4 py-2 text-sm text-[#d4af37]"
      >
        {pending ? t('listingInquiry.sending') : t('listingInquiry.send')}
      </button>
      {msg ? <p className="mt-2 text-sm text-[#cbb98a]">{msg}</p> : null}
    </div>
  );
}
