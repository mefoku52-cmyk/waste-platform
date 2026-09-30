"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { DashboardFooter } from "@/components/layout/dashboard-footer";
import {
  useAdminUserActivity,
  useAdminUserSummary,
} from "@/features/admin";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const BG = "#090807";
const FG = "#f3ead8";
const MUTED = "#9a8f7c";

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("sk-SK");
  } catch {
    return iso;
  }
}

function statusColor(status: string | undefined): string {
  if (!status) return "bg-gray-100 text-gray-700";
  const s = status.toLowerCase();
  if (["active", "aktivny", "aktívny"].includes(s))
    return "bg-green-100 text-green-800";
  if (["pending_verification", "invited"].includes(s))
    return "bg-yellow-100 text-yellow-800";
  if (["suspended", "deactivated", "inactive"].includes(s))
    return "bg-red-100 text-red-800";
  return "bg-gray-100 text-gray-700";
}

export default function AdminUserDetailPage() {
  const params = useParams();
  const userId = typeof params?.id === "string" ? params.id : undefined;

  const { data: summary, isLoading, error } = useAdminUserSummary(userId);
  const { data: activity } = useAdminUserActivity(userId, 100);

  if (isLoading) {
    return (
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />
        <div className="mx-auto max-w-5xl px-4 py-16 text-center" style={{ color: MUTED }}>
          Načítavam používateľa…
        </div>
        <DashboardFooter />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        <DashboardHeader />
        <main className="mx-auto max-w-5xl px-4 py-10">
          <Link
            href="/dashboard/admin"
            className="text-sm hover:underline"
            style={{ color: GOLD_BRIGHT }}
          >
            ← Späť na admin
          </Link>
          <p className="mt-4 text-red-400">
            Používateľ sa nenašiel alebo chyba načítania.
          </p>
        </main>
        <DashboardFooter />
      </div>
    );
  }

  const { user, counts } = summary;
  const activityItems = activity?.items ?? [];

  return (
    <div className="min-h-screen" style={{ background: BG, color: FG }}>
      <DashboardHeader />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <Link
          href="/dashboard/admin"
          className="text-sm hover:underline"
          style={{ color: GOLD_BRIGHT }}
        >
          ← Späť na admin panel
        </Link>

        {/* Profil */}
        <div className="mt-6 rounded-xl border border-[#d4af37]/20 bg-[#0f0e0c] p-6">
          <h1 className="font-serif text-3xl text-[#f3ead8]">
            {[user.firstName, user.lastName].filter(Boolean).join(" ") ||
              user.email}
          </h1>
          <p className="mt-1 text-sm text-[#9a8f7c]">{user.email}</p>
          <div className="mt-4 flex flex-wrap gap-3 text-xs">
            <span
              className={
                "inline-flex items-center rounded-full px-3 py-1 font-medium " +
                statusColor(user.status)
              }
            >
              {user.status}
            </span>
            <span className="inline-flex items-center rounded-full bg-[#1a1814] px-3 py-1 text-[#9a8f7c]">
              ID: {user.id.slice(0, 8)}…
            </span>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <div className="text-xs uppercase tracking-wider text-[#9a8f7c]">
                Vytvorený
              </div>
              <div className="mt-1 text-sm">{formatDate(user.createdAt)}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider text-[#9a8f7c]">
                Posledné prihlásenie
              </div>
              <div className="mt-1 text-sm">{formatDate(user.lastLoginAt)}</div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Listingy", value: counts.listings },
            { label: "Dopyty", value: counts.inquiries },
            { label: "Členstvá", value: counts.memberships },
            { label: "Eventov", value: counts.activity_events },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-[#d4af37]/20 bg-[#0f0e0c] p-4"
            >
              <div className="text-xs uppercase tracking-wider text-[#9a8f7c]">
                {item.label}
              </div>
              <div className="mt-1 text-2xl font-semibold text-[#f3ead8]">
                {item.value ?? 0}
              </div>
            </div>
          ))}
        </div>

        {/* Activity timeline */}
        <div className="mt-6 rounded-xl border border-[#d4af37]/20 bg-[#0f0e0c] p-6">
          <h2 className="font-serif text-2xl text-[#f3ead8]">
            Aktivita používateľa
          </h2>
          <p className="mt-1 text-sm text-[#9a8f7c]">
            Posledných {activityItems.length} udalostí
          </p>

          {activityItems.length === 0 ? (
            <p className="mt-4 text-sm italic text-[#9a8f7c]">
              Žiadna aktivita.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {activityItems.map((item) => (
                <li
                  key={item.id}
                  className="rounded-lg border border-[#d4af37]/10 bg-[#141210] p-3"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-mono text-xs text-[#e8d48b]">
                      {item.eventType}
                    </span>
                    <span className="text-xs text-[#9a8f7c]">
                      {formatDate(item.createdAt)}
                    </span>
                  </div>
                  {item.payload ? (
                    <div className="mt-1 text-xs text-[#9a8f7c] line-clamp-2">
                      {item.payload}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
      <DashboardFooter />
    </div>
  );
}
