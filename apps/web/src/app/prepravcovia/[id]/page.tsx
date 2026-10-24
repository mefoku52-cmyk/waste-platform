"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { config } from "@/lib/config";

const GOLD = "#c9a84c";
const MUTED = "#9a8f7c";

export default function TransportDetailPage() {
  const params = useParams<{ id: string }>();
  const offerId = String(params?.id || "");

  const query = useQuery({
    queryKey: ["transport-offer", offerId],
    queryFn: async () => {
      const res = await fetch(`${config.apiBaseUrl}/transport/offers`);
      const data = await res.json();
      const offer = data.find((o: any) => o.id === offerId);
      if (!offer) throw new Error("Ponuka sa nenašla");
      return offer;
    },
    enabled: Boolean(offerId),
  });

  if (query.isLoading) return <p className="p-8 text-center" style={{ color: MUTED }}>Načítavam...</p>;
  if (query.error) return <p className="p-8 text-center text-red-500">Ponuka sa nenašla.</p>;

  const offer = query.data;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link href="/prepravcovia" className="mb-6 inline-block text-sm" style={{ color: GOLD }}>
        ← Späť na prepravcov
      </Link>

      <div className="rounded-2xl border p-6" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
        <h1 className="mb-2 font-serif text-3xl" style={{ color: GOLD }}>
          {offer.title}
        </h1>
        <p className="mb-4 text-sm" style={{ color: MUTED }}>
          {offer.transportFrom} → {offer.transportTo || "kamkoľvek"}
        </p>

        <div className="mb-6 flex flex-wrap gap-2 text-sm">
          <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>
            {offer.vehicleType}
          </span>
          {offer.capacityTons && <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>{offer.capacityTons} t</span>}
          {offer.pricePerKm && <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>{offer.pricePerKm} EUR/km</span>}
          {offer.hasAdr && <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>ADR</span>}
          {offer.hasRefrigeration && <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>Chladenie</span>}
          {offer.hasHydraulicArm && <span className="rounded-full px-3 py-1" style={{ background: "rgba(201,168,76,0.15)", color: GOLD }}>Hydraulická ruka</span>}
        </div>

        {offer.description && (
          <div className="mb-6">
            <h2 className="mb-2 text-lg font-semibold" style={{ color: GOLD }}>Popis služby</h2>
            <p className="text-sm" style={{ color: "#f3e6c4" }}>{offer.description}</p>
          </div>
        )}

        {offer.hazardousTypes && offer.hazardousTypes.length > 0 && (
          <div className="mb-6">
            <h2 className="mb-2 text-lg font-semibold" style={{ color: "#ff6b6b" }}>Nebezpečný odpad</h2>
            <div className="flex flex-wrap gap-2">
              {offer.hazardousTypes.map((h: string) => (
                <span key={h} className="rounded-full px-3 py-1 text-sm" style={{ background: "rgba(255,0,0,0.15)", color: "#ff6b6b" }}>
                  {h === "biohazard" ? "Biohazard" : h === "hospital_waste" ? "Nemocničný odpad" : h === "acids" ? "Kyseliny" : h === "chemicals" ? "Chemikálie" : h === "infectious" ? "Infekčný materiál" : h === "radioactive" ? "Rádioaktívny" : h === "flammable" ? "Horľaviny" : h === "toxic" ? "Toxické" : h}
                </span>
              ))}
            </div>
          </div>
        )}
        
        <div className="mt-8 rounded-xl border p-4" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
          <p className="text-sm font-semibold mb-2" style={{ color: GOLD }}>Máte záujem o túto prepravu?</p>
          <p className="text-xs mb-4" style={{ color: MUTED }}>Kontaktujte firmu priamo a dohodnite si podmienky.</p>
          <button
            type="button"
            className="w-full rounded-xl py-3 font-semibold transition hover:opacity-90"
            style={{ background: GOLD, color: "#0b0b0b" }}
            onClick={() => alert("Funkcia odoslania dopytu bude doplnená čoskoro.")}
          >
            Poslať dopyt
          </button>
        </div>
      </div>
    </div>
  );
}
