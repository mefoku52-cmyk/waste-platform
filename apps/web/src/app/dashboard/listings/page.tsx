"use client";

import { ListingsTable } from "@/features/listings";

export default function MyListingsPage() {
  return (
    <main className="mx-auto max-w-5xl p-6">
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
