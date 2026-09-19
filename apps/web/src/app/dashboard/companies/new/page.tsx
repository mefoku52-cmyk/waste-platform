'use client';

import { DashboardHeader } from '@/components/layout/dashboard-header';
import { CompanyForm } from '@/features/companies';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';

export default function NewCompanyPage() {
  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <DashboardHeader />

        <main className="mx-auto max-w-2xl px-4 py-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            NOVÁ FIRMA
          </p>
          <h1 className="mb-8 text-4xl leading-tight tracking-[-0.02em] md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Pridať firmu
          </h1>
          <CompanyForm />
        </main>
      </div>
    </>
  );
}
