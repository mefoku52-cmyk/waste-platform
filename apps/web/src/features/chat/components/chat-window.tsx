'use client';

import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useMessages, useThread } from '../hooks/use-threads';
import { chatApi } from '../api';
import { useCurrentUser } from '../../auth/hooks/use-current-user';

export const ChatWindow = ({ threadId }: { threadId: string }) => {
  const qc = useQueryClient();
  const { data: thread } = useThread(threadId);
  const { data: msgs, isLoading } = useMessages(threadId);
  const { data: me } = useCurrentUser();
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const myId = String(
    (me as any)?.id || (me as any)?.user?.id || '',
  );

  useEffect(() => {
    chatApi.markRead(threadId).catch(() => {});
  }, [threadId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const send = async () => {
    if (!text.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      await chatApi.sendMessage(threadId, text.trim());
      setText('');
      await qc.invalidateQueries({ queryKey: ['chat-messages', threadId] });
      await qc.invalidateQueries({ queryKey: ['chat-threads'] });
    } catch (e: any) {
      setErr(e?.message || 'Odoslanie zlyhalo');
    } finally {
      setBusy(false);
    }
  };

  if (isLoading) return <div className="p-6 text-slate-400">Načítavam správy...</div>;

  const items = (msgs as any)?.items ?? [];
  const subject = (thread as any)?.data?.subject || 'Konverzácia';

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-700 px-4 py-3">
        <h2 className="text-lg font-semibold text-slate-100">{subject}</h2>
        <p className="text-xs text-slate-400">
          Telefóny a emaily sú v správe automaticky skryté.
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {items.length === 0 ? (
          <p className="text-sm text-slate-500">Žiadne správy. Napíš prvú.</p>
        ) : (
          items.map((m: any) => {
            const mine = String(m.senderUserId) === myId;
            return (
              <div
                key={m.id}
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                  mine
                    ? 'ml-auto bg-emerald-600 text-white'
                    : 'bg-slate-800 text-slate-100'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">{m.body}</div>
                <div className="mt-1 text-[10px] opacity-70">
                  {new Date(m.createdAt).toLocaleString('sk-SK')}
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-slate-700 p-3">
        {err && <div className="mb-2 text-xs text-red-400">{err}</div>}
        <div className="flex gap-2">
          <textarea
            className="flex-1 resize-none rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-emerald-400"
            rows={2}
            placeholder="Napíš správu..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            type="button"
            disabled={busy || !text.trim()}
            onClick={send}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {busy ? '...' : 'Poslať'}
          </button>
        </div>
      </div>
    </div>
  );
};
