'use client';

import { InquiriesTable } from '@/features/inquiries/components/inquiries-table';

export default function InquiriesPage() {
  return (
    <main className="mx-auto w-full max-w-6xl bg-[#070707] p-6 text-[#f3e6c4]">
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#d4af37]">Dopyty</p>
      <h1 className="mt-1 font-serif text-3xl">Prijate</h1>
      <div className="mt-4">
        <InquiriesTable mode="received" />
      </div>
      <h2 className="mt-10 font-serif text-2xl">Odoslane</h2>
      <div className="mt-4">
        <InquiriesTable mode="sent" />
      </div>
    </main>
  );
}
