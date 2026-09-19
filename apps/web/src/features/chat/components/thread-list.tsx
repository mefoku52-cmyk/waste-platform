'use client';

import Link from 'next/link';
import { useThreads } from '../hooks/use-chat-queries';

export const ThreadList = ({ activeId }: { activeId?: string }) => {
  const { data, isLoading } = useThreads();
  const items = (data as any)?.items ?? [];

  if (isLoading) return <div className="p-4 text-sm text-slate-500">Načítavam...</div>;

  if (items.length === 0) {
    return (
      <div className="p-4 text-sm text-slate-500">
        Zatiaľ žiadne konverzácie. Začni chat z detailu ponuky.
      </div>
    );
  }

  return (
    <ul className="divide-y divide-slate-700">
      {items.map((t: any) => {
        const isActive = String(t.id) === String(activeId);
        const when = t.lastMessageAt
          ? new Date(t.lastMessageAt).toLocaleString('sk-SK')
          : '';
        return (
          <li key={t.id}>
            <Link
              href={`/dashboard/chat/${t.id}`}
              className={`block px-4 py-3 transition ${
                isActive ? 'bg-slate-800' : 'hover:bg-slate-800/60'
              }`}
            >
              <div className="font-medium text-slate-100 truncate">{t.subject}</div>
              <div className="mt-1 text-xs text-slate-400 truncate">{when}</div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
};
