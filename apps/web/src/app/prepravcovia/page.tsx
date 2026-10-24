"use client";

import { useQuery } from "@tanstack/react-query";
import { config } from "@/lib/config";

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
      <p className="mb-6 text-sm" style={{ color: MUTED }}>
        Aktuálne ponuky dopravy a logistiky od overených firiem.
      </p>

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
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
