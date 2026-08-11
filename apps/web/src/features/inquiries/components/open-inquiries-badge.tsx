'use client';

import { useReceivedInquiries } from '../hooks/use-inquiries';

export const OpenInquiriesBadge = () => {
  const { data } = useReceivedInquiries();
  const items = (data as any)?.items ?? [];
  const openCount = items.filter((i: any) => i.status === 'open').length;
  if (openCount <= 0) return null;
  return (
    <span className="ml-2 inline-flex items-center rounded-full bg-red-600 px-2.5 py-0.5 text-xs font-semibold text-white">
      {openCount} nový
    </span>
  );
};
