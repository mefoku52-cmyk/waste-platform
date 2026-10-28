"use client";

import { useRouter } from "next/navigation";
import { config } from "@/lib/config";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";
const BG = "#0b0b0b";

export default function SubscriptionPage() {
  const router = useRouter();

  async function handleSelectPlan(tier: string) {
    try {
      const token = localStorage.getItem("accessToken");
      // Získame company_id používateľa
      let companyId = null;
      try {
        const meRes = await fetch(`${config.apiBaseUrl}/auth/me`, {
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        });
        if (meRes.ok) {
          const me = await meRes.json();
          const memberships = me.memberships || [];
          if (memberships.length > 0) {
            companyId = memberships[0].companyId;
          }
        }
      } catch {}
      
      const res = await fetch(`${config.apiBaseUrl}/billing/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          tier: tier,
          company_id: companyId,
          success_url: window.location.origin + "/dashboard/subscription?success=true",
          cancel_url: window.location.origin + "/dashboard/subscription?canceled=true",
        }),
      });
      const data = await res.json();
      if (data.checkout_url || data.url) {
        window.location.href = data.checkout_url || data.url;
      } else {
        alert("Chyba pri vytváraní platby: " + JSON.stringify(data));
      }
    } catch (e: any) {
      alert("Chyba: " + e.message);
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: BG }}>
      {/* Hero sekcia s fotkou */}
      <div className="relative h-72 w-full overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&q=80"
          alt="Predplatné"
          className="h-full w-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#0b0b0b]" />
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
          <h1 className="font-serif text-5xl md:text-6xl" style={{ color: GOLD_BRIGHT }}>
            Predplatné
          </h1>
          <p className="mt-4 max-w-2xl text-sm md:text-base" style={{ color: MUTED }}>
            Získajte viac. Rozšírte svoje možnosti. Využite silu AI a inteligentnej navigácie na maximum.
          </p>
        </div>
      </div>

      {/* Karty */}
      <div className="relative z-10 mx-auto -mt-16 max-w-6xl px-4 pb-16">
        <div className="grid gap-6 md:grid-cols-3">
          {/* FREE */}
          <div className="rounded-3xl border p-8 backdrop-blur-md transition hover:scale-105" style={{ borderColor: "rgba(201,168,76,0.25)", background: "rgba(11,11,11,0.7)" }}>
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-full border-2" style={{ borderColor: GOLD }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold" style={{ color: GOLD_BRIGHT }}>FREE</h2>
            <p className="mt-1 text-sm" style={{ color: MUTED }}>Základné funkcie pre každého</p>
            <p className="mt-6 text-4xl font-bold" style={{ color: GOLD }}>0 € <span className="text-sm font-normal" style={{ color: MUTED }}>/ mesiac</span></p>
            <ul className="mt-6 space-y-3 text-sm" style={{ color: "#f3e6c4" }}>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Prístup k základnej platforme</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Zobrazenie ponúk a dopytov</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Základná komunikácia v chate</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Obmedzenia na AI správy</li>
            </ul>
            <button className="mt-8 w-full rounded-xl border py-3 text-sm font-semibold transition hover:bg-[rgba(201,168,76,0.1)]" style={{ borderColor: GOLD, color: GOLD }}>
              Aktuálny plán
            </button>
          </div>

          {/* AI */}
          <div className="rounded-3xl border-2 p-8 backdrop-blur-md transition hover:scale-105 shadow-2xl" style={{ borderColor: GOLD, background: "rgba(11,11,11,0.8)", boxShadow: "0 0 40px rgba(201,168,76,0.2)" }}>
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-full border-2" style={{ borderColor: GOLD }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2">
                <path d="M12 2a3 3 0 0 0-3 3v1H7a3 3 0 0 0-3 3v1H3v6h1v1a3 3 0 0 0 3 3h1v1a3 3 0 0 0 3 3h2a3 3 0 0 0 3-3v-1h1a3 3 0 0 0 3-3v-1h1v-6h-1V9a3 3 0 0 0-3-3h-1V5a3 3 0 0 0-3-3h-2z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold" style={{ color: GOLD_BRIGHT }}>AI</h2>
            <p className="mt-1 text-sm" style={{ color: MUTED }}>Inteligentný asistent pre vašu prácu</p>
            <p className="mt-6 text-4xl font-bold" style={{ color: GOLD }}>29 € <span className="text-sm font-normal" style={{ color: MUTED }}>/ mesiac</span></p>
            <ul className="mt-6 space-y-3 text-sm" style={{ color: "#f3e6c4" }}>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Všetko z plánu FREE</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> AI chat bez limitu</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Inteligentné vyhľadávanie a analýzy</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Rýchlejšia práca s ponukami a dopytmi</li>
              <li className="flex items-start gap-2"><span style={{ color: GOLD }}>✓</span> Automatické dopĺňanie údajov</li>
            </ul>
            <button onClick={() => handleSelectPlan("ai")} className="mt-8 w-full rounded-xl py-3 text-sm font-semibold transition hover:opacity-90" style={{ background: GOLD, color: "#0b0b0b" }}>
              Vybrať plán
            </button>
          </div>

          {/* AI NAVIGÁCIA */}
          <div className="rounded-3xl border-2 p-8 backdrop-blur-md transition hover:scale-105 shadow-2xl" style={{ borderColor: "#2dd4bf", background: "rgba(11,11,11,0.8)", boxShadow: "0 0 40px rgba(45,212,191,0.2)" }}>
            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-full border-2" style={{ borderColor: "#2dd4bf" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2dd4bf" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold" style={{ color: GOLD_BRIGHT }}>AI Navigácia</h2>
            <p className="mt-1 text-sm" style={{ color: MUTED }}>Kompletný asistent s navigáciou</p>
            <p className="mt-6 text-4xl font-bold" style={{ color: GOLD }}>99 € <span className="text-sm font-normal" style={{ color: MUTED }}>/ mesiac</span></p>
            <ul className="mt-6 space-y-3 text-sm" style={{ color: "#f3e6c4" }}>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Všetko z plánu AI</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Aktívny AI asistent – rozumie kontextu a sám koná</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Otvorí stránky (ponuky, dopyty, firmy) na tvoj príkaz</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Vyplní formuláre za teba (ponuka, dopyt, profil)</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Odošle po tvojom súhlase (dopyty, správy)</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Navigácia – mapy, trasy, vzdialenosti</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Predikcia nákladov a času</li>
              <li className="flex items-start gap-2"><span style={{ color: "#2dd4bf" }}>✓</span> Plná integrácia do platformy</li>
            </ul>
            <button onClick={() => handleSelectPlan("ai_navigation")} className="mt-8 w-full rounded-xl py-3 text-sm font-semibold transition hover:opacity-90" style={{ background: "#2dd4bf", color: "#0b0b0b" }}>
              Vybrať plán
            </button>
          </div>
        </div>

        {/* Sekcia Vyskúšaj zadarmo */}
        <div className="mt-16 rounded-3xl border-2 p-8 backdrop-blur-md" style={{ borderColor: "rgba(45,212,191,0.5)", background: "rgba(11,11,11,0.8)", boxShadow: "0 0 40px rgba(45,212,191,0.15)" }}>
          <div className="flex flex-col items-center gap-6 md:flex-row md:justify-between">
            <div className="flex-1 text-center md:text-left">
              <h2 className="font-serif text-3xl md:text-4xl" style={{ color: GOLD_BRIGHT }}>
                Vyskúšajte AI Navigáciu zadarmo
              </h2>
              <p className="mt-3 text-sm md:text-base" style={{ color: MUTED }}>
                Presvedčte sa, ako vám AI navigácia uľahčí prácu. Ukážeme vám 2 kroky, ako AI za vás otvorí ponuky, vyplní formulár a odošle dopyt. Bezplatne, bez záväzkov.
              </p>
            </div>
            <div className="flex-shrink-0">
              <a
                href="/dashboard/ai-demo"
                className="inline-flex items-center gap-2 rounded-xl px-8 py-4 text-base font-semibold transition hover:scale-105"
                style={{ background: "#2dd4bf", color: "#0b0b0b" }}
              >
                Vyskúšať zadarmo
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
