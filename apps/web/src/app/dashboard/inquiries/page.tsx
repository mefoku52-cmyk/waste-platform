"use client";

import { PremiumHero } from "@/components/layout/premium-hero";

const MUTED = "#9a8f7c";

export default function InquiriesPage() {
  return (
    <div className="min-h-screen" style={{ background: "#0b0b0b" }}>
      <PremiumHero
        title="Dopyty"
        subtitle="Prijaté a odoslané dopyty. Reaguj rýchlo a nezmeškaj obchod."
        imageUrl="https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1600&q=80"
      />
      <div className="mx-auto max-w-5xl px-4 py-8 -mt-12 relative z-10">
        <div className="rounded-2xl border p-6" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
          <p style={{ color: MUTED }}>Obsah stránky Dopyty (bude doplnený).</p>
        </div>
      </div>
    </div>
  );
}
