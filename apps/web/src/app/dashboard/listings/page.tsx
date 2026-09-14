"use client";

import { ListingsTable } from "@/features/listings";
import Link from "next/link";

export default function MyListingsPage() {
  return (
    <main className="mx-auto max-w-5xl p-6">
      <Link
        href="/dashboard"
        className="mb-4 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-800"
      >
        ← Späť na dashboard
      </Link>

      <header className="mb-6">
        <h1 className="text-2xl font-bold">Moje ponuky</h1>
        <p className="mt-1 text-sm text-slate-500">
          Spravuj svoje ponuky. Publikovať môže len firma so statusom{" "}
          <strong>verified</strong>.
        </p>
      </header>
      <ListingsTable />
    </main>
  );
}
