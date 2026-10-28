"use client";

import Link from "next/link";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";
const BG = "#0b0b0b";

export default function SubscriptionPage() {
  return (
    <div className="min-h-screen p-6" style={{ background: BG }}>
      <div className="mx-auto max-w-5xl">
        <div className="mb-8 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full border-2" style={{ borderColor: GOLD }}>
            <span className="text-2xl"></span>
          </div>
          <div>
            <h1 className="font-serif text-4xl" style={{ color: GOLD_BRIGHT }}>Predplatné</h1>
            <p className="mt-1 text-sm" style={{ color: MUTED }}>
              Získajte viac. Rozšírte svoje možnosti. Využite silu AI a inteligentnej navigácie na maximum.
            </p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {/* FREE */}
          <div className="rounded-2xl border p-6" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border" style={{ borderColor: GOLD }}>
              <span className="text-xl"></span>
            </div>
            <h2 className="text-2xl font-bold" style={{ color: GOLD_BRIGHT }}>FREE</h2>
            <p className="text-sm" style={{ color: MUTED }}>Základné funkcie pre každého</p>
            <p className="mt-4 text-3xl font-bold" style={{ color: GOLD }}>0 € <span className="text-sm font-normal">/ mesiac</span></p>
            <ul className="mt-4 space-y-2 text-sm" style={{ color: "#f3e6c4" }}>
              <li>✓ Prístup k základnej platforme</li>
              <li>✓ Zobrazenie ponúk a dopytov</li>
              <li>✓ Základná komunikácia v chate</li>
              <li>✓ Obmedzenia na AI správy</li>
            </ul>
            <button className="mt-6 w-full rounded-lg border py-2 text-sm font-semibold" style={{ borderColor: GOLD, color: GOLD }}>
              Aktuálny plán
            </button>
          </div>

          {/* AI */}
          <div className="rounded-2xl border-2 p-6" style={{ borderColor: GOLD }}>
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border" style={{ borderColor: GOLD }}>
              <span className="text-xl"></span>
            </div>
            <h2 className="text-2xl font-bold" style={{ color: GOLD_BRIGHT }}>AI</h2>
            <p className="text-sm" style={{ color: MUTED }}>Inteligentný asistent pre vašu prácu</p>
            <p className="mt-4 text-3xl font-bold" style={{ color: GOLD }}>29 € <span className="text-sm font-normal">/ mesiac</span></p>
            <ul className="mt-4 space-y-2 text-sm" style={{ color: "#f3e6c4" }}>
              <li>✓ Všetko z plánu FREE</li>
              <li>✓ AI chat bez limitu</li>
              <li>✓ Inteligentné vyhľadávanie a analýzy</li>
              <li>✓ Rýchlejšia práca s ponukami a dopytmi</li>
              <li>✓ Automatické dopĺňanie údajov</li>
            </ul>
            <button className="mt-6 w-full rounded-lg py-2 text-sm font-semibold" style={{ background: GOLD, color: "#0b0b0b" }}>
              Vybrať plán
            </button>
          </div>

          {/* AI NAVIGÁCIA */}
          <div className="rounded-2xl border-2 p-6" style={{ borderColor: "#2dd4bf" }}>
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border" style={{ borderColor: "#2dd4bf" }}>
              <span className="text-xl"></span>
            </div>
            <h2 className="text-2xl font-bold" style={{ color: GOLD_BRIGHT }}>AI Navigácia</h2>
            <p className="text-sm" style={{ color: MUTED }}>Kompletný asistent s navigáciou</p>
            <p className="mt-4 text-3xl font-bold" style={{ color: GOLD }}>59 € <span className="text-sm font-normal">/ mesiac</span></p>
            <ul className="mt-4 space-y-2 text-sm" style={{ color: "#f3e6c4" }}>
              <li>✓ Všetko z plánu AI</li>
              <li>✓ AI navigácia (komet-like)</li>
              <li>✓ Otvorenie máp, trasy, vzdialenosti</li>
              <li>✓ Predikcia nákladov a času</li>
              <li>✓ Automatické odporúčania</li>
              <li>✓ Plná integrácia do platformy</li>
            </ul>
            <button className="mt-6 w-full rounded-lg py-2 text-sm font-semibold" style={{ background: "#2dd4bf", color: "#0b0b0b" }}>
              Vybrať plán
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
