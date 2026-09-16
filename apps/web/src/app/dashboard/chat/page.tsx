'use client';

import Link from 'next/link';
import { ThreadList } from '@/features/chat';

export default function ChatPage() {
  return (
    <main className="mx-auto max-w-5xl p-6">
      <Link
        href="/dashboard"
        className="mb-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800"
      >
        ← Späť na dashboard
      </Link>

      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Chat</h1>
        <p className="mt-1 text-sm text-slate-400">
          Konverzácie s ostatnými firmami. Telefóny a emaily sú skryté.
        </p>
      </header>

      <div className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
        <ThreadList />
      </div>
    </main>
  );
}
