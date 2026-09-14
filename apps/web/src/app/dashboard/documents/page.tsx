"use client";

import Link from "next/link";
import { DocumentsTable } from "@/features/documents";

export default function DocumentsPage() {
  return (
    <main className="mx-auto max-w-5xl p-6">
      <Link
        href="/dashboard"
        className="mb-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800"
      >
        ← Späť na dashboard
      </Link>

      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Dokumenty</h1>
          <p className="mt-1 text-sm text-slate-500">
            Certifikáty, povolenia a ďalšie dokumenty tvojich firiem.
          </p>
        </div>

        <Link
          href="/dashboard/documents/new"
          className="rounded-lg border border-emerald-600 bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
        >
          + Pridať dokument
        </Link>
      </header>

      <DocumentsTable />
    </main>
  );
}
