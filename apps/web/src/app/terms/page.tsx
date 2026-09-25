'use client';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function TermsPage() {
  return (
    <>
      <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet" />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <header className="border-b" style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}>
          <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'Fraunces, serif', fontSize: '1.25rem' }}>CMEP</span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/privacy" style={{ color: MUTED }}>Súkromie</Link>
              <Link href="/license" style={{ color: MUTED }}>Licencia</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PRÁVNE</p>
          <h1 className="mb-10 text-4xl md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Obchodné podmienky
          </h1>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>1. Prevádzkovateľ</h2>
              <p>Platformu CMEP (Circular Materials Exchange Platform) prevádzkuje:</p>
              <ul className="mt-3 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>2. Predmet platformy</h2>
              <p>
                CMEP je B2B platforma určená na sprostredkovanie kontaktu medzi firmami, ktoré ponúkajú
                a dopytujú obehové materiály (druhotné suroviny, prebytky z výroby, vedľajšie produkty).
                Platforma <strong style={{ color: FG }}>nie je obchodníkom</strong> ani stranou v obchodnom vzťahu.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>3. Registrácia a účet</h2>
              <p>Používateľ je povinný pri registrácii uvádzať pravdivé údaje. Za správnosť údajov zodpovedá výhradne používateľ.</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>4. Zodpovednosť za obsah</h2>
              <p>
                Platforma <strong style={{ color: FG }}>nenesie zodpovednosť</strong> za pravdivosť, úplnosť ani zákonnosť inzerátov vložených používateľmi.
                Používateľ nesmie zverejňovať osobné údaje tretích osôb bez ich súhlasu.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>5. Riešenie sporov</h2>
              <p>
                Spory medzi používateľmi sa riešia priamo medzi nimi. Platforma môže na žiadosť poskytnúť
                súčinnosť, ale nie je arbitrom.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>6. Zmeny podmienok</h2>
              <p>Prevádzkovateľ si vyhradzuje právo meniť tieto podmienky. O zmenách budú používatelia informovaní e-mailom alebo notifikáciou v platforme.</p>
            </section>

            <p className="pt-8 text-sm" style={{ color: '#6e6658' }}>
              Posledná aktualizácia: {new Date().toLocaleDateString('sk-SK')}
            </p>
          </div>
        </main>
      </div>
    </>
  );
}
