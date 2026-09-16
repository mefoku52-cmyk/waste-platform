'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ThreadList, ChatWindow } from '@/features/chat';

export default function ChatThreadPage() {
  const params = useParams();
  const id = String(params?.id || '');

  return (
    <main className="mx-auto max-w-6xl p-6">
      <Link
        href="/dashboard/chat"
        className="mb-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800"
      >
        ← Späť na zoznam
      </Link>

      <div className="grid gap-4 md:grid-cols-[300px_1fr]">
        <aside className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
          <ThreadList activeId={id} />
        </aside>
        <section className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden h-[600px]">
          {id ? <ChatWindow threadId={id} /> : null}
        </section>
      </div>
    </main>
  );
}
