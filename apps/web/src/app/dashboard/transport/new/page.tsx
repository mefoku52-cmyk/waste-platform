"use client";

import { tokenStore } from '@/lib/auth/token-store';

import { useState } from "react";
import { useRouter } from "next/navigation";
import { config } from "@/lib/config";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";
const BG = "#0b0b0b";

const CATEGORIES = [
  { id: "truck", label: "Kamiónová preprava", desc: "Veľké náklady, 24 ton, ADR" },
  { id: "personal", label: "Osobná preprava", desc: "Dodávky, sťahovanie, menšie náklady" },
  { id: "business", label: "Hospodárska preprava", desc: "Materiál, palety, stavebný materiál" },
  { id: "parcel", label: "Baličková preprava", desc: "Menšie balíky, kurýrske služby" },
];

export default function NewTransportPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<string[]>(["truck"]);
  const [form, setForm] = useState({
    title: "",
    transportFrom: "",
    transportTo: "",
    vehicleType: "",
    capacityTons: "",
    pricePerKm: "",
    hasAdr: false,
    hasRefrigeration: false,
    hasHydraulicArm: false,
    hazardousTypes: [] as string[],
    availableFrom: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function toggleCategory(id: string) {
    setCategories((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function toggleHazardous(id: string) {
    setForm((prev) => ({
      ...prev,
      hazardousTypes: prev.hazardousTypes.includes(id)
        ? prev.hazardousTypes.filter((x) => x !== id)
        : [...prev.hazardousTypes, id],
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    if (categories.length === 0) {
      setError("Vyberte aspoň jednu kategóriu.");
      return;
    }

    try {
      const token = tokenStore.getToken();
      const meRes = await fetch(`${config.apiBaseUrl}/auth/me`, {
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      const me = await meRes.json();
      const companyId = me.memberships?.[0]?.companyId;
      if (!companyId) {
        setError("Najprv si musíte vytvoriť firmu v sekcii 'Pridať firmu'.");
        return;
      }

      const res = await fetch(`${config.apiBaseUrl}/transport/offers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          title: form.title,
          categories: categories,
          transportFrom: form.transportFrom,
          transportTo: form.transportTo,
          vehicleType: form.vehicleType,
          capacityTons: form.capacityTons ? parseFloat(form.capacityTons) : null,
          pricePerKm: form.pricePerKm ? parseFloat(form.pricePerKm) : null,
          hasRefrigeration: form.hasRefrigeration,
          hasAdr: form.hasAdr,
          hasHydraulicArm: form.hasHydraulicArm,
          hazardousTypes: form.hazardousTypes,
          availableFrom: form.availableFrom || null,
          companyId: companyId,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => router.push("/prepravcovia"), 1500);
      } else {
        setError(JSON.stringify(data));
      }
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div className="min-h-screen p-6" style={{ background: BG }}>
      <div className="mx-auto max-w-3xl">
        <h1 className="mb-6 font-serif text-4xl" style={{ color: GOLD_BRIGHT }}>
          Pridať službu
        </h1>

        {error && (
          <div className="mb-4 rounded-xl border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-300">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-xl border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-300">
            ✅ Služba bola odoslaná na schválenie. Po schválení adminom sa zobrazí v zozname.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Kategórie (viacero) */}
          <div>
            <label className="mb-2 block text-sm font-semibold" style={{ color: GOLD }}>
              Kategórie služby (môžete vybrať viacero)
            </label>
            <div className="grid grid-cols-2 gap-3">
              {CATEGORIES.map((cat) => (
                <label
                  key={cat.id}
                  className="flex cursor-pointer items-start gap-2 rounded-xl border p-3 transition"
                  style={{
                    borderColor: categories.includes(cat.id) ? GOLD : "rgba(201,168,76,0.25)",
                    background: categories.includes(cat.id) ? "rgba(201,168,76,0.1)" : "transparent",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={categories.includes(cat.id)}
                    onChange={() => toggleCategory(cat.id)}
                    className="mt-1 h-4 w-4"
                  />
                  <div>
                    <p className="font-semibold" style={{ color: GOLD_BRIGHT }}>{cat.label}</p>
                    <p className="text-xs" style={{ color: MUTED }}>{cat.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Názov */}
          <div>
            <label className="mb-1 block text-sm" style={{ color: MUTED }}>Názov ponuky</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
              className="w-full rounded-lg border p-2 text-sm"
              style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }}
              placeholder="Preprava z Košíc do Bratislavy"
            />
          </div>

          {/* Odkiaľ - Kam */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Odkiaľ</label>
              <input type="text" value={form.transportFrom} onChange={(e) => setForm({ ...form, transportFrom: e.target.value })} required className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} placeholder="Košice" />
            </div>
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Kam</label>
              <input type="text" value={form.transportTo} onChange={(e) => setForm({ ...form, transportTo: e.target.value })} className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} placeholder="Bratislava (alebo prázdne = kamkoľvek)" />
            </div>
          </div>

          {/* Vozidlo a cena */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Typ vozidla</label>
              <input type="text" value={form.vehicleType} onChange={(e) => setForm({ ...form, vehicleType: e.target.value })} className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} placeholder="kamión" />
            </div>
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Cena za km (EUR)</label>
              <input type="number" step="0.1" value={form.pricePerKm} onChange={(e) => setForm({ ...form, pricePerKm: e.target.value })} className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} placeholder="1.5" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Kapacita (tony)</label>
              <input type="number" value={form.capacityTons} onChange={(e) => setForm({ ...form, capacityTons: e.target.value })} className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} placeholder="24" />
            </div>
            <div>
              <label className="mb-1 block text-sm" style={{ color: MUTED }}>Dostupné od</label>
              <input type="date" value={form.availableFrom} onChange={(e) => setForm({ ...form, availableFrom: e.target.value })} className="w-full rounded-lg border p-2 text-sm" style={{ borderColor: "rgba(201,168,76,0.25)", background: "#0b0b0b", color: "#f3e6c4" }} />
            </div>
          </div>

          {/* Checkboxy */}
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.hasAdr} onChange={(e) => setForm({ ...form, hasAdr: e.target.checked })} className="h-4 w-4" />
              ADR (nebezpečný tovar)
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.hasRefrigeration} onChange={(e) => setForm({ ...form, hasRefrigeration: e.target.checked })} className="h-4 w-4" />
              Chladiaci box
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.hasHydraulicArm} onChange={(e) => setForm({ ...form, hasHydraulicArm: e.target.checked })} className="h-4 w-4" />
              Hydraulická ruka
            </label>
          </div>

          {/* Nebezpečný odpad */}
          <div>
            <label className="mb-2 block text-sm font-semibold" style={{ color: GOLD }}>Nebezpečný odpad (ADR)</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "biohazard", label: "Biohazard" },
                { id: "hospital_waste", label: "Nemocničný odpad" },
                { id: "acids", label: "Kyseliny" },
                { id: "chemicals", label: "Chemikálie" },
                { id: "infectious", label: "Infekčný materiál" },
                { id: "radioactive", label: "Rádioaktívny" },
                { id: "flammable", label: "Horľaviny" },
                { id: "toxic", label: "Toxické" },
              ].map((h) => (
                <label key={h.id} className="flex items-center gap-2 rounded-lg border p-2 text-sm cursor-pointer" style={{ borderColor: form.hazardousTypes.includes(h.id) ? GOLD : "rgba(201,168,76,0.25)" }}>
                  <input type="checkbox" checked={form.hazardousTypes.includes(h.id)} onChange={() => toggleHazardous(h.id)} className="h-4 w-4" />
                  {h.label}
                </label>
              ))}
            </div>
          </div>

          <button type="submit" className="w-full rounded-xl py-3 text-sm font-semibold" style={{ background: GOLD, color: "#0b0b0b" }}>
            Odoslať na schválenie
          </button>
        </form>
      </div>
    </div>
  );
}
