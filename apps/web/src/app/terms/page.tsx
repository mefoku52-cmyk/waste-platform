'use client';
import Link from 'next/link';
import { useT } from '@/lib/i18n/context';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function TermsPage() {
  const { t } = useT();
  return (
    <>
      <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap" rel="stylesheet" />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <header className="border-b" style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}>
          <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: '1.25rem' }}>CMEP</span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/privacy" style={{ color: MUTED }}>{t('legal.privacy')}</Link>
              <Link href="/license" style={{ color: MUTED }}>{t('legal.license')}</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PRÁVNE</p>
          <h1 className="mb-10 text-4xl md:text-5xl" style={{ fontFamily: 'DM Serif Display, serif' }}>
            Obchodné podmienky
          </h1>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>1. Prevádzkovateľ</h2>
              <p>Platformu CMEP (Circular Materials Exchange Platform) prevádzkuje:</p>
              <ul className="mt-3 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>2. Predmet platformy</h2>
              <p>
                CMEP je B2B platforma určená na sprostredkovanie kontaktu medzi firmami, ktoré ponúkajú
                a dopytujú obehové materiály (druhotné suroviny, prebytky z výroby, vedľajšie produkty).
                Platforma <strong style={{ color: FG }}>nie je obchodníkom</strong> ani stranou v obchodnom vzťahu.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>3. Registrácia a účet</h2>
              <p>Používateľ je povinný pri registrácii uvádzať pravdivé údaje. Za správnosť údajov zodpovedá výhradne používateľ.</p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>4. Zodpovednosť za obsah</h2>
              <p>
                Platforma <strong style={{ color: FG }}>nenesie zodpovednosť</strong> za pravdivosť, úplnosť ani zákonnosť inzerátov vložených používateľmi.
                Používateľ nesmie zverejňovať osobné údaje tretích osôb bez ich súhlasu.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>5. Platené služby a topovanie</h2>
              <p>
                Platforma ponúka dobrovoľné platené zvýraznenie ponúk (tzv. „topovanie"). Ceny sú uvedené v EUR s DPH:
              </p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li><strong style={{ color: FG }}>TOP 7 dní</strong> — 5,00 €</li>
                <li><strong style={{ color: FG }}>TOP 30 dní</strong> — 10,00 €</li>
                <li><strong style={{ color: FG }}>GOLD 30 dní</strong> — 30,00 € (zlatý rámik + navrchu 30 dní)</li>
              </ul>
              <p className="mt-3">
                Po zaplatení je služba aktivovaná okamžite a je neodvolateľná.
                <strong style={{ color: FG }}> Zrušenie po aktivácii nie je možné</strong> a nárok na vrátenie peňazí zaniká.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>6. Spôsob platby</h2>
              <p>
                Platby spracúva spoločnosť <strong style={{ color: FG }}>GoPay</strong> (GoPay s.r.o., IČO: 260 46 745), ktorá je licencovanou platobnou inštitúciou.
                Pri platbe môžeš použiť platobnú kartu (Visa, Mastercard), Apple Pay, Google Pay alebo bankový prevod.
              </p>
              <p className="mt-3">
                Platforma nemá prístup k údajom o tvojej platobnej karte. Všetky platobné údaje spracúva výhradne GoPay.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>7. Fakturácia a daňový doklad</h2>
              <p>
                Po úspešnej platbe bude daňový doklad (faktúra) vygenerovaný automaticky a zaslaný na e-mail uvedený v používateľskom účte.
                Faktúra obsahuje identifikačné údaje firmy (IČO, DIČ, adresa) a je v súlade so zákonom č. 222/2004 Z. z. o DPH.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>8. Riešenie sporov</h2>
              <p>
                Spory medzi používateľmi sa riešia priamo medzi nimi. Platforma môže na žiadosť poskytnúť
                súčinnosť, ale nie je arbitrom.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'DM Serif Display, serif' }}>9. Zmeny podmienok</h2>
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
