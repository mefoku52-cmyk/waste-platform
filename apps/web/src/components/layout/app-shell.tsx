import { ReactNode } from "react";

function RailCard({ title, hint }: { title: string; hint: string }) {
  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{title}</p>
      </div>
      <div className="flex min-h-[140px] items-center justify-center px-3 py-6 text-center">
        <p className="text-xs text-slate-400">{hint}</p>
      </div>
    </section>
  );
}

export function AppShell({
  header,
  children,
}: {
  header: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#eef3ee]">
      {header}
      <div className="border-b border-amber-200/70 bg-amber-50">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-3 py-2 sm:px-6">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-900">Granty a výzvy</p>
          <p className="truncate text-xs text-amber-800/90">Priestor pre aktuálne výzvy a partnerov</p>
        </div>
      </div>
      <div className="mx-auto grid max-w-7xl gap-4 px-3 py-4 sm:px-6 sm:py-6 lg:grid-cols-[minmax(0,1fr)_240px]">
        <div className="min-w-0 space-y-4 sm:space-y-6">{children}</div>
        <aside className="hidden space-y-4 lg:block">
          <RailCard title="Sponzori" hint="Logo partnera 200×80" />
          <RailCard title="Reklama" hint="Banner 240×400" />
        </aside>
      </div>
    </div>
  );
}
