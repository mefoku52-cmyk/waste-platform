"use client";

import Link from "next/link";
import { ReactNode } from "react";

import { useThreads } from "../hooks/use-chat-queries";
import { useT } from "@/lib/i18n/context";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";
const BG = "#090807";
const PANEL = "#0f0e0c";

type Thread = {
  id: string;
  lastMessage?: string | null;
  last_message?: string | null;
  unreadCount?: number;
  unread_count?: number;
  subject?: string | null;
  companyName?: string | null;
  company_name?: string | null;
};

function getSubject(t: Thread): string {
  return t.subject || t.companyName || t.company_name || "Firma";
}

function getLastMessage(t: Thread): string {
  return t.lastMessage || t.last_message || "";
}

function getUnread(t: Thread): number {
  return Number(t.unreadCount ?? t.unread_count ?? 0);
}

export function ChatShell({
  activeThreadId,
  children,
}: {
  activeThreadId?: string;
  children: ReactNode;
}) {
  const { t } = useT();
  const query = useThreads() as {
    data?: unknown;
    isLoading?: boolean;
    error?: unknown;
  };
  const raw = query.data as
    | { items?: Thread[]; data?: Thread[] | { items?: Thread[] } }
    | Thread[]
    | undefined;
  const items: Thread[] = Array.isArray(raw)
    ? raw
    : raw?.items ?? (Array.isArray(raw?.data) ? raw.data : raw?.data?.items ?? []);

  return (
    <div
      className="mx-auto flex w-full max-w-6xl flex-col md:h-[calc(100vh-9rem)] md:flex-row"
      style={{ background: BG }}
    >
      {/* SIDEBAR — skryjem na mobile ked je aktivny thread */}
      <aside
        className={
          "w-full shrink-0 border-b md:w-[300px] md:border-b-0 md:border-r " +
          (activeThreadId ? "hidden md:block" : "block")
        }
        style={{ borderColor: "color-mix(in srgb, #c9a84c 20%, transparent)" }}
      >
        <div
          className="px-4 py-4"
          style={{ borderBottom: "1px solid color-mix(in srgb, #c9a84c 15%, transparent)" }}
        >
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.22em]"
            style={{ color: GOLD }}
          >
            {t("chat.section")}
          </p>
          <h1
            className="mt-1 font-serif text-2xl leading-tight"
            style={{ color: GOLD_BRIGHT }}
          >
            {t("chat.title")}
          </h1>
        </div>

        <div className="overflow-y-auto md:h-[calc(100%-5.5rem)]">
          {query.isLoading ? (
            <p className="p-4 text-sm" style={{ color: MUTED }}>
              {t("chat.loading")}
            </p>
          ) : query.error ? (
            <p className="p-4 text-sm text-red-300">{t("chat.loadError")}</p>
          ) : items.length === 0 ? (
            <p className="p-4 text-sm" style={{ color: MUTED }}>
              {t("chat.empty")}
            </p>
          ) : (
            <ul>
              {items.map((thread) => {
                const active = thread.id === activeThreadId;
                const unread = getUnread(thread);
                return (
                  <li key={thread.id}>
                    <Link
                      href={`/dashboard/chat/${thread.id}`}
                      className="block px-4 py-3 transition-colors"
                      style={{
                        background: active
                          ? "rgba(201,168,76,0.12)"
                          : "transparent",
                        borderLeft: active
                          ? `3px solid ${GOLD}`
                          : "3px solid transparent",
                        borderBottom:
                          "1px solid color-mix(in srgb, #c9a84c 8%, transparent)",
                      }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p
                          className="truncate text-sm font-semibold"
                          style={{ color: active ? GOLD_BRIGHT : "#f3ead8" }}
                        >
                          {getSubject(thread)}
                        </p>
                        {unread > 0 ? (
                          <span
                            className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold"
                            style={{ background: GOLD, color: BG }}
                          >
                            {unread}
                          </span>
                        ) : null}
                      </div>
                      <p
                        className="mt-1 truncate text-xs"
                        style={{ color: MUTED }}
                      >
                        {getLastMessage(thread) || "—"}
                      </p>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>

      {/* OBSAH — konverzacia alebo empty state */}
      <section
        className={
          "flex min-h-[60vh] flex-1 flex-col " +
          (activeThreadId ? "flex" : "hidden md:flex")
        }
        style={{ background: PANEL }}
      >
        {children}
      </section>
    </div>
  );
}
