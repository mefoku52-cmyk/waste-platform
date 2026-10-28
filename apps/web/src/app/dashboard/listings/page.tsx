"use client";

import Link from "next/link";
import { PremiumHero } from "@/components/layout/premium-hero";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

export default function ListingsPage() {
  return (
    <div className="min-h-screen" style={{ background: "#0b0b0b" }}>
      <PremiumHero
        title="Ponuky"
        subtitle="Trhovisko materiálov a moje ponuky. Predávaj alebo kupuj obehové materiály."
        imageUrl="https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1600&q=80"
      />
      <div className="mx-auto max-w-5xl px-4 py-8 -mt-12 relative z-10">
        <div className="rounded-2xl border p-6" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
          <p style={{ color: MUTED }}>Obsah stránky Ponuky (bude doplnený).</p>
          <Link href="/dashboard/listings/new" className="mt-4 inline-block rounded-full px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: "#0b0b0b" }}>
            + Pridať ponuku
          </Link>
        </div>
      </div>
    </div>
  );
}
