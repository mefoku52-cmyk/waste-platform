import { ReactNode } from "react";

function RailCard({ title, hint }: { title: string; hint: string }) {
  return (
    <section className="rounded-md bg-white/80 px-2 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{title}</p>
      <p className="mt-1 text-[11px] text-slate-400">{hint}</p>
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
    <div className="relative min-h-screen bg-[#eef3ee]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[url('/rc-mark.png')] bg-no-repeat bg-center bg-cover opacity-30"
      />
      {header}
      <div className="border-b border-amber-200/70 bg-amber-50">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-3 py-2 sm:px-6">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-900">Granty a výzvy</p>
          <p className="truncate text-xs text-amber-800/90">Priestor pre aktuálne výzvy a partnerov</p>
        </div>
      </div>
      <div className="mx-auto grid max-w-7xl gap-3 px-3 py-3 sm:px-6 lg:grid-cols-[minmax(0,1fr)_200px]">
        <div className="min-w-0 space-y-3">{children}</div>
        <aside className="hidden space-y-4 lg:block">
          <RailCard title="Sponzori" hint="Logo partnera 200×80" />
          <RailCard title="Reklama" hint="Banner 240×400" />
        </aside>
      </div>
    </div>
  );
}
