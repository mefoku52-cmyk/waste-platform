'use client';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function PrivacyPage() {
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
              <Link href="/terms" style={{ color: MUTED }}>Podmienky</Link>
              <Link href="/license" style={{ color: MUTED }}>Licencia</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PRÁVNE</p>
          <h1 className="mb-10 text-4xl md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Ochrana osobných údajov
          </h1>

          <div className="space-y-8 text-base leading-relaxed" style={{ color: MUTED }}>
            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>1. Správca údajov</h2>
              <p>Správcom osobných údajov je:</p>
              <ul className="mt-3 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>2. Aké údaje zbierame</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>E-mail, meno, rola v platforme</li>
                <li>Údaje o firme: IČO, DIČ, adresa, kontaktné údaje</li>
                <li>Obsah inzerátov, ktoré vložíte</li>
                <li>Technické údaje: IP adresa, typ zariadenia, čas prihlásenia</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>3. Na aký účel</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>Poskytovanie služieb platformy (registrácia, prihlásenie, inzeráty)</li>
                <li>Overenie firiem a IČO</li>
                <li>Zasielanie notifikácií o dopytoch a správach</li>
                <li>Bezpečnosť a prevencia podvodov</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>4. Ako dlho uchovávame</h2>
              <p>
                Údaje uchovávame po dobu existencie účtu, maximálne však 3 roky od poslednej aktivity.
                Po vymazaní účtu sa osobné údaje anonymizujú alebo vymažú, okrem údajov, ktoré musíme
                uchovať zo zákona (napr. účtovné doklady).
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>5. Vaše práva</h2>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>Právo na prístup k svojim údajom</li>
                <li>Právo na opravu nesprávnych údajov</li>
                <li>Právo na vymazanie („právo byť zabudnutý")</li>
                <li>Právo namietať spracúvanie</li>
                <li>Právo podať sťažnosť na Úrad na ochranu osobných údajov SR</li>
              </ul>
              <p className="mt-3">
                Žiadosti posielajte na <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a>. Odpovieme do 30 dní.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>6. Cookies</h2>
              <p>
                Platforma používa nevyhnutné cookies na prihlásenie a zabezpečenie relácie.
                Nepoužívame reklamné ani tracking cookies tretích strán.
              </p>
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
