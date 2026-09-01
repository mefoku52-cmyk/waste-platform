'use client';

import { Logo } from "@/components/brand/logo";

import { MatchesPanel } from "@/features/listings";
import { ComplianceTable } from "@/features/compliance";
import { AuditTable } from "@/features/admin";
import { DocumentsTable } from "@/features/documents";
import { useAuthRequired } from "@/features/auth";
import { useLogout } from "@/features/auth";
import { Button } from "@/components/ui/button";
import { ListingsTable } from "@/features/listings";
import { NotificationsPanel } from "@/features/notifications";
import { MarketplaceTable } from "@/features/listings";
import { InquiriesTable } from "@/features/inquiries";
import { OpenInquiriesBadge } from "@/features/inquiries";
import { CompaniesTable } from "@/features/companies";
import { useRouter } from "next/navigation";

const nav = [
  { href: "#ponuky", label: "Ponuky" },
  { href: "#trhovisko", label: "Trhovisko" },
  { href: "#zhody", label: "Zhody" },
  { href: "#prijate", label: "Prijaté" },
  { href: "#odoslane", label: "Odoslané" },
  { href: "#firmy", label: "Firmy" },
  { href: "#dokumenty", label: "Dokumenty" },
  { href: "#audit", label: "Audit" },
  { href: "#compliance", label: "Compliance" },
];

function SectionCard({
  id,
  title,
  action,
  children,
  subtitle,
}: {
  id: string;
  title: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
  subtitle?: string;
}) {
  return (
    <section id={id} className="scroll-mt-28 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-emerald-50/40 px-4 py-3 sm:px-5">
        <div>
          <h2 className="text-base font-semibold tracking-tight text-slate-900 sm:text-lg">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="p-3 sm:p-4">{children}</div>
    </section>
  );
}

export default function DashboardPage() {
  const { user, isLoading } = useAuthRequired();
  const { mutate: logout, isPending: isLoggingOut } = useLogout();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="text-sm font-medium text-slate-500">Načítavam…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 via-slate-50 to-emerald-50/30">
      {/* sticky top */}
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-3 py-3 sm:px-6">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-700">CMEP</p>
            <h1 className="truncate text-base font-bold text-slate-900 sm:text-xl">
              Obehové materiály
            </h1>
            {user?.role === "admin" && (
              <button
                type="button"
                onClick={() => router.push("/dashboard/admin")}
                className="text-[11px] font-medium text-emerald-700 hover:underline"
              >
                Admin panel →
              </button>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <div className="hidden text-right xs:block sm:block">
              <p className="max-w-[140px] truncate text-xs font-medium text-slate-800 sm:max-w-[200px] sm:text-sm">
                {user?.email}
              </p>
              <p className="text-[10px] capitalize text-slate-500">{user?.role || "user"}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="border-slate-200 text-slate-700"
              onClick={() => logout()}
              disabled={isLoggingOut}
            >
              {isLoggingOut ? "…" : "Odhlásiť"}
            </Button>
          </div>
        </div>

        {/* mobile nav chips */}
        <div className="border-t border-slate-100">
          <div className="mx-auto flex max-w-6xl gap-2 overflow-x-auto px-3 py-2.5 scrollbar-none sm:px-6">
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="shrink-0 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-800 active:scale-[0.98]"
              >
                {item.label}
              </a>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-4 px-3 py-4 sm:space-y-6 sm:px-6 sm:py-8">
        <div className="overflow-hidden rounded-2xl border border-emerald-100 bg-white shadow-sm">
          <div className="border-b border-emerald-50 bg-emerald-50/50 px-4 py-2.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Notifikácie</p>
          </div>
          <div className="p-3 sm:p-4">
            <NotificationsPanel />
          </div>
        </div>

        <SectionCard
          id="ponuky"
          title="Aktuálne ponuky"
          action={
            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => router.push("/dashboard/listings/new")}>
              + Ponuka
            </Button>
          }
        >
          <ListingsTable />
        </SectionCard>

        <SectionCard id="trhovisko" title="Trhovisko" subtitle="Publikované ponuky od iných firiem">
          <MarketplaceTable />
        </SectionCard>

        <SectionCard id="zhody" title="Odporúčané zhody" subtitle="Podľa typu materiálu tvojich ponúk">
          <MatchesPanel />
        </SectionCard>

        <SectionCard
          id="prijate"
          title={
            <span className="inline-flex items-center gap-2">
              Prijaté dopyty <OpenInquiriesBadge />
            </span>
          }
        >
          <InquiriesTable mode="received" />
        </SectionCard>

        <SectionCard id="odoslane" title="Odoslané dopyty">
          <InquiriesTable mode="sent" />
        </SectionCard>

        <SectionCard
          id="firmy"
          title="Registrované firmy"
          action={
            <Button size="sm" variant="secondary" onClick={() => router.push("/dashboard/companies/new")}>
              + Firma
            </Button>
          }
        >
          <CompaniesTable />
        </SectionCard>

        <SectionCard
          id="dokumenty"
          title="Dokumenty"
          action={
            <Button size="sm" variant="secondary" onClick={() => router.push("/dashboard/documents/new")}>
              + Dokument
            </Button>
          }
        >
          <DocumentsTable />
        </SectionCard>

        <SectionCard id="audit" title="Audit log">
          <AuditTable />
        </SectionCard>

        <SectionCard id="compliance" title="Compliance">
          <ComplianceTable />
        </SectionCard>

        <p className="pb-6 text-center text-[11px] text-slate-400">CMEP · lokálny vývoj</p>
      </main>
    </div>
  );
}
