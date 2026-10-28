"use client";

import { useState } from "react";
import Link from "next/link";

const GOLD = "#c9a84c";
const GOLD_BRIGHT = "#e8d48b";
const MUTED = "#9a8f7c";
const BG = "#0b0b0b";

export default function AiDemoPage() {
  const [step, setStep] = useState(0);
  const [message, setMessage] = useState("");

  const steps = [
    { title: "Krok 1: Otvor ponuky", desc: "AI asistent otvorí zoznam ponúk na platforme." },
    { title: "Krok 2: Vyplň formulár", desc: "AI vyplní formulár za teba (názov, popis, množstvo)." },
    { title: "Krok 3: Odošli dopyt", desc: "AI odošle dopyt po tvojom súhlase." },
  ];

  function handleNext() {
    if (step < steps.length - 1) {
      setStep(step + 1);
      setMessage(`✅ ${steps[step].title} – hotovo!`);
    } else {
      setMessage("🎉 Ukážka dokončená! Toto všetko vie AI Navigácia za 99 €/mesiac.");
    }
  }

  return (
    <div className="min-h-screen p-6" style={{ background: BG }}>
      <div className="mx-auto max-w-3xl">
        <Link href="/dashboard/subscription" className="mb-6 inline-block text-sm" style={{ color: GOLD }}>
          ← Späť na predplatné
        </Link>

        <h1 className="mb-4 font-serif text-4xl" style={{ color: GOLD_BRIGHT }}>
          Ukážka AI Navigácie
        </h1>
        <p className="mb-8 text-sm" style={{ color: MUTED }}>
          Toto je ukážka, ako AI asistent pracuje. Ukážeme ti 3 kroky, ako za teba otvorí ponuky, vyplní formulár a odošle dopyt.
        </p>

        <div className="space-y-4">
          {steps.map((s, i) => (
            <div key={i} className="rounded-xl border p-4" style={{ borderColor: i <= step ? GOLD : "rgba(201,168,76,0.25)", opacity: i <= step ? 1 : 0.5 }}>
              <h3 className="font-semibold" style={{ color: i <= step ? GOLD : MUTED }}>
                {i <= step ? "✅" : "○"} {s.title}
              </h3>
              <p className="mt-1 text-sm" style={{ color: MUTED }}>{s.desc}</p>
            </div>
          ))}
        </div>

        {message && (
          <div className="mt-6 rounded-xl border p-4" style={{ borderColor: GOLD, background: "rgba(201,168,76,0.1)" }}>
            <p className="text-sm" style={{ color: GOLD_BRIGHT }}>{message}</p>
          </div>
        )}

        <button
          onClick={handleNext}
          className="mt-8 w-full rounded-xl py-3 text-sm font-semibold transition hover:opacity-90"
          style={{ background: GOLD, color: "#0b0b0b" }}
        >
          {step < steps.length - 1 ? "Pokračovať" : "Dokončiť ukážku"}
        </button>

        {step >= steps.length - 1 && (
          <Link href="/dashboard/subscription" className="mt-4 block w-full rounded-xl border py-3 text-center text-sm font-semibold" style={{ borderColor: GOLD, color: GOLD }}>
            Chcem AI Navigáciu za 99 €
          </Link>
        )}
      </div>
    </div>
  );
}
