"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { config } from "@/lib/config";
import { PremiumHero } from "@/components/layout/premium-hero";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

type TransportOffer = {
  id: string;
  title: string;
  transportFrom: string;
  transportTo?: string | null;
  vehicleType: string;
  capacityTons?: number | null;
  pricePerKm?: number | null;
  currency: string;
  hasAdr: boolean;
  hazardousTypes?: string[];
};

async function fetchTransportOffers(): Promise<TransportOffer[]> {
  const res = await fetch(`${config.apiBaseUrl}/transport/offers`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export default function CarriersPage() {
  const { data: me } = useCurrentUser();
  const isLoggedIn = Boolean(me && (me as any).id);

  const { data, isLoading, error } = useQuery({
    queryKey: ["transport-offers"],
    queryFn: fetchTransportOffers,
  });

  const offers = data || [];

  return (
    <div className="min-h-screen" style={{ background: "#0b0b0b" }}>
      <PremiumHero
        title="Prepravcovia"
        subtitle="Doprava, logistika a skladovanie. Nájdite spoľahlivého prepravcu pre váš materiál."
        imageUrl="https://images.unsplash.com/photo-1519003722824-194d4455a60c?w=1600&q=80"
      />

      <div className="mx-auto max-w-5xl px-4 py-8 -mt-12 relative z-10">
        {isLoggedIn && (
          <div className="mb-6 flex justify-end">
            <Link
              href="/dashboard/transport/new"
              className="rounded-full px-6 py-3 text-sm font-semibold transition hover:scale-105"
              style={{ background: GOLD, color: "#0b0b0b" }}
            >
              + Pridať službu
            </Link>
          </div>
        )}

        {isLoading ? (
          <p style={{ color: MUTED }}>Načítavam ponuky dopravy...</p>
        ) : error ? (
          <p style={{ color: "red" }}>Chyba: {(error as Error).message}</p>
        ) : offers.length === 0 ? (
          <p style={{ color: MUTED }}>Zatiaľ žiadne ponuky dopravy.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {offers.map((offer) => (
              <Link
                key={offer.id}
                href={`/prepravcovia/${offer.id}`}
                className="block rounded-2xl border p-5 sm:p-6 transition hover:border-[#c9a84c]"
                style={{ borderColor: "rgba(201,168,76,0.25)" }}
              >
                <h2 className="font-semibold" style={{ color: GOLD }}>{offer.title}</h2>
                <p className="mt-1 text-sm" style={{ color: MUTED }}>
                  {offer.transportFrom} → {offer.transportTo || "kamkoľvek"}
                </p>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>{offer.vehicleType}</span>
                  {offer.capacityTons && <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>{offer.capacityTons} t</span>}
                  {offer.pricePerKm && <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>{offer.pricePerKm} EUR/km</span>}
                  {offer.hasAdr && <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>ADR</span>}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
