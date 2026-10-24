"use client";

import { useQuery } from "@tanstack/react-query";
import { config } from "@/lib/config";
import Link from "next/link";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

type TransportOffer = {
  id: string;
  title: string;
  description?: string | null;
  transportFrom: string;
  transportTo?: string | null;
  vehicleType: string;
  capacityTons?: number | null;
  pricePerKm?: number | null;
  currency: string;
  hasRefrigeration: boolean;
  hasAdr: boolean;
  hasHydraulicArm: boolean;
  hazardousTypes: string[];
  createdAt: string;
};

async function fetchTransportOffers(): Promise<TransportOffer[]> {
  const res = await fetch(`${config.apiBaseUrl}/transport/offers`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
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
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-2 font-serif text-3xl" style={{ color: GOLD }}>
        Prepravcovia
      </h1>
      <div className="mb-6 h-48 w-full overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.25)]">
        <img 
          src="https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=1200&q=80" 
          alt="Prepravcovia" 
          className="h-full w-full object-cover" 
        />
      </div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm" style={{ color: MUTED }}>
          Aktuálne ponuky dopravy a logistiky od overených firiem.
        </p>
        {isLoggedIn && (
          <Link
            href="/dashboard/company/transport"
            className="rounded-full px-4 py-2 text-sm font-semibold transition hover:opacity-90"
            style={{ background: GOLD, color: "#0b0b0b" }}
          >
            + Pridať dopravnú službu
          </Link>
        )}
      </div>

      {isLoading ? (
        <p style={{ color: MUTED }}>Načítavam ponuky dopravy...</p>
      ) : error ? (
        <p style={{ color: "red" }}>Chyba pri načítaní: {error.message}</p>
      ) : offers.length === 0 ? (
        <p style={{ color: MUTED }}>Zatiaľ žiadne ponuky dopravy.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {offers.map((offer) => (
            <div
              key={offer.id}
              className="rounded-xl border p-4 transition hover:border-[#c9a84c]"
              style={{ borderColor: "rgba(201,168,76,0.25)" }}
            >
              <h2 className="font-semibold" style={{ color: GOLD }}>
                {offer.title}
              </h2>
              <p className="mt-1 text-sm" style={{ color: MUTED }}>
                {offer.transportFrom} → {offer.transportTo || "kamkoľvek"}
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                  {offer.vehicleType}
                </span>
                {offer.capacityTons && (
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                    {offer.capacityTons} t
                  </span>
                )}
                {offer.pricePerKm && (
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                    {offer.pricePerKm} {offer.currency}/km
                  </span>
                )}
                {offer.hasAdr && (
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                    ADR
                  </span>
                )}
                {offer.hasHydraulicArm && (
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                    Hydraulická ruka
                  </span>
                )}
                {offer.hasRefrigeration && (
                  <span className="rounded-full px-2 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
                    Chladenie
                  </span>
                )}
                {offer.hazardousTypes && offer.hazardousTypes.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    <span className="text-xs font-semibold" style={{ color: GOLD }}>Nebezpečný odpad:</span>
                    {offer.hazardousTypes.map((h) => (
                      <span key={h} className="rounded-full px-2 py-0.5 text-xs" style={{ background: "rgba(255,0,0,0.15)", color: "#ff6b6b" }}>
                        {h === "biohazard" ? "Biohazard" :
                         h === "hospital_waste" ? "Nemocničný odpad" :
                         h === "acids" ? "Kyseliny" :
                         h === "chemicals" ? "Chemikálie" :
                         h === "infectious" ? "Infekčný materiál" :
                         h === "radioactive" ? "Rádioaktívny" :
                         h === "flammable" ? "Horľaviny" :
                         h === "toxic" ? "Toxické" : h}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
