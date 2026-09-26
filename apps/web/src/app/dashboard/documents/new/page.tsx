'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { DashboardFooter } from '@/components/layout/dashboard-footer';
import { DocumentForm } from '@/features/documents';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';

export default function NewDocumentPage() {
  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-2xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            NOVÝ DOKUMENT
          </p>
          <h1 className="mb-8 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            Pridať dokument
          </h1>
          <DocumentForm />
        </main>

      <DashboardFooter />
      </div>
    </>
  );
}
