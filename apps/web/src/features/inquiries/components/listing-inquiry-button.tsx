'use client';

import { useState } from 'react';
import { inquiriesApi } from '../api';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';

export function ListingInquiryButton({
  listingId,
  listingTitle,
}: {
  listingId: string;
  listingTitle?: string;
}) {
  const me = useCurrentUser();
  const [pending, setPending] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const companyId = me.data?.memberships?.[0]?.companyId;
  const email = me.data?.email || '';

  const send = async () => {
    if (!companyId) {
      setMsg('Najprv si zaloz a over firmu.');
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
      setMsg('Dopyt odoslany.');
    } catch (e: unknown) {
      const text =
        e instanceof Error
          ? e.message
          : typeof e === 'object' && e && 'message' in e
            ? String((e as { message: unknown }).message)
            : 'Dopyt zlyhal';
      setMsg(text);
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
        {pending ? 'Posielam dopyt…' : 'Poslat dopyt'}
      </button>
      {msg ? <p className="mt-2 text-sm text-[#cbb98a]">{msg}</p> : null}
    </div>
  );
}
