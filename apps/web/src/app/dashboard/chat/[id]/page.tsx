"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ChatShell } from "@/features/chat/components/chat-shell";
import { useMarkRead, useMessages, useSendMessage } from "@/features/chat";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useT } from "@/lib/i18n/context";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const FG = "#f3ead8";
const MUTED = "#9a8f7c";
const DANGER = "#f0bbb0";

type Message = {
  id: string;
  body?: string;
  senderUserId?: string;
  sender_user_id?: string;
  createdAt?: string;
  created_at?: string;
};

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const hm = d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
    });
    return d.toLocaleDateString() + " " + hm;
  } catch {
    return "";
  }
}

export default function ChatThreadPage() {
  const params = useParams<{ id: string }>();
  const id = String(params?.id || "");
  const { t } = useT();
  const { data: me } = useCurrentUser();
  const [draft, setDraft] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const messagesQuery = useMessages(id) as { data?: unknown; isLoading?: boolean };
  const sendMutation = useSendMessage(id);
  const markReadMutation = useMarkRead();

  const myId = String((me as any)?.id || (me as any)?.user?.id || "");

  const raw = messagesQuery.data as
    | { items?: Message[]; data?: Message[] | { items?: Message[] } }
    | Message[]
    | undefined;
  const items: Message[] = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  useEffect(() => {
    if (id) markReadMutation.mutate(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [items.length]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;
    setErrorMessage("");
    try {
      await sendMutation.mutateAsync(body);
      setDraft("");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t("common.error"));
    }
  }

  return (
    <AppShell>
      <ChatShell activeThreadId={id}>
        {/* HEADER na mobile — back link */}
        <div
          className="flex items-center gap-3 border-b px-4 py-3 md:hidden"
          style={{ borderColor: "color-mix(in srgb, #c9a84c 20%, transparent)" }}
        >
          <Link
            href="/dashboard/chat"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border text-sm"
            style={{
              borderColor: "color-mix(in srgb, #c9a84c 40%, transparent)",
              color: GOLD_BRIGHT,
            }}
            aria-label={t("common.back")}
          >
            ←
          </Link>
          <p
            className="truncate font-serif text-lg"
            style={{ color: GOLD_BRIGHT }}
          >
            {t("chat.conversation")}
          </p>
        </div>

        {/* MESSAGES */}
        <div className="flex-1 space-y-1 overflow-y-auto px-4 py-4 sm:px-5">
          {messagesQuery.isLoading ? (
            <div className="space-y-3">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-12 w-2/3 animate-pulse rounded-2xl"
                  style={{ background: "rgba(201,168,76,0.08)" }}
                />
              ))}
              <p className="text-center text-xs" style={{ color: MUTED }}>
                {t("chat.loading")}
              </p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="font-serif text-lg" style={{ color: GOLD_BRIGHT }}>
                {t("chat.empty")}
              </p>
              <p className="mt-1 text-xs" style={{ color: MUTED }}>
                {t("chat.emptyHint")}
              </p>
            </div>
          ) : (
            items.map((message, idx) => {
              const sender = String(
                message.senderUserId || message.sender_user_id || "",
              );
              const mine = !!myId && sender === myId;
              const prev = idx > 0 ? items[idx - 1] : null;
              const prevSender = prev
                ? String(prev.senderUserId || prev.sender_user_id || "")
                : "";
              const sameSender = !!prev && prevSender === sender;
              const date = message.createdAt || message.created_at || "";

              return (
                <div key={message.id} className={sameSender ? "mt-1" : "mt-4"}>
                  <div
                    className={
                      "max-w-[78%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed " +
                      (mine ? "ml-auto" : "mr-auto")
                    }
                    style={
                      mine
                        ? {
                            background: `linear-gradient(135deg, ${GOLD} 0%, ${GOLD_BRIGHT} 100%)`,
                            color: "#090807",
                          }
                        : {
                            background: "rgba(201,168,76,0.08)",
                            border:
                              "1px solid color-mix(in srgb, #c9a84c 30%, transparent)",
                            color: FG,
                          }
                    }
                  >
                    {!sameSender && (
                      <div
                        className={
                          "mb-1 text-[10px] font-semibold uppercase tracking-wider " +
                          (mine ? "text-right" : "text-left")
                        }
                        style={{ color: mine ? "rgba(9,8,7,0.75)" : GOLD }}
                      >
                        {mine ? "Vy" : "Druhá firma"}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap break-words">
                      {message.body || ""}
                    </div>
                    <div
                      className={
                        "mt-1 text-[10px] " + (mine ? "text-right" : "text-left")
                      }
                      style={{ color: mine ? "rgba(9,8,7,0.65)" : MUTED }}
                    >
                      {date ? formatTime(date) : ""}
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={bottomRef} />
        </div>

        {/* INPUT */}
        <form
          onSubmit={onSubmit}
          className="border-t p-3 sm:p-4"
          style={{ borderColor: "color-mix(in srgb, #c9a84c 25%, transparent)" }}
        >
          {errorMessage ? (
            <div className="mb-2 text-xs" style={{ color: DANGER }}>
              {errorMessage}
            </div>
          ) : null}
          <div className="flex items-end gap-2">
            <textarea
              rows={2}
              placeholder={t("chat.sendPlaceholder")}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  onSubmit(e as unknown as FormEvent);
                }
              }}
              disabled={sendMutation.isPending}
              className="flex-1 resize-none rounded-xl border px-3 py-2 text-sm outline-none"
              style={{
                borderColor: "color-mix(in srgb, #c9a84c 25%, transparent)",
                background: "#0b0b0b",
                color: FG,
              }}
            />
            <button
              type="submit"
              disabled={sendMutation.isPending || !draft.trim()}
              className="rounded-xl px-4 py-2 text-sm font-semibold transition disabled:opacity-40"
              style={{ background: GOLD, color: "#090807" }}
            >
              {sendMutation.isPending ? t("chat.sending") : t("chat.send")}
            </button>
          </div>
        </form>
      </ChatShell>
    </AppShell>
  );
}
