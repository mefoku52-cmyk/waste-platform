'use client';
import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

export default function LicensePage() {
  const year = new Date().getFullYear();
  const today = new Date().toLocaleDateString('sk-SK');

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
              <Link href="/privacy" style={{ color: MUTED }}>Súkromie</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PRÁVNE</p>
          <h1 className="mb-4 text-4xl md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Licencia a autorské práva
          </h1>
          <p className="mb-10 text-sm" style={{ color: FAINT }}>
            Verzia 1.0 · Účinná od {today} · © {year} Radoslav Čornanič
          </p>

          <div className="space-y-10 text-base leading-relaxed" style={{ color: MUTED }}>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>1. Vlastníctvo platformy</h2>
              <p>
                Platforma <strong style={{ color: FG }}>CMEP</strong> (Circular Materials Exchange Platform),
                vrátane zdrojového kódu, dizajnu, textov, databázovej štruktúry, API, loga TRČ, vizuálnej identity
                a všetkých súvisiacich autorských diel, je <strong style={{ color: GOLD_BRIGHT }}>výhradným duševným vlastníctvom</strong> prevádzkovateľa:
              </p>
              <ul className="mt-4 space-y-1">
                <li><strong style={{ color: FG }}>Radoslav Čornanič</strong></li>
                <li>IČO: 51745666</li>
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
              <p className="mt-4">
                Všetky práva, ktoré nie sú výslovne udelené touto licenciou, zostávajú vyhradené prevádzkovateľovi.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>2. Predmet licencie</h2>
              <p>Táto licencia sa vzťahuje na:</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>Zdrojový kód platformy (frontend aj backend)</li>
                <li>Dizajn, UI/UX, farebnú schému, typografiu</li>
                <li>Logo TRČ a vizuálnu identitu</li>
                <li>Texty, popisy, marketingové materiály</li>
                <li>Databázovú schému a štruktúru</li>
                <li>API a dokumentáciu</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>3. Udelená licencia používateľom</h2>
              <p>
                Používateľom platformy sa udeľuje <strong style={{ color: FG }}>nevýhradná, neprenosná,
                odvolateľná a časovo obmedzená licencia</strong> na používanie platformy výhradne na účel
                sprostredkovania obehových materiálov (predaj, dopyt, komunikácia medzi firmami).
              </p>
              <p className="mt-3">Táto licencia <strong style={{ color: FG }}>neoprávňuje</strong> používateľa:</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>Kopírovať, distribuovať alebo predávať zdrojový kód platformy</li>
                <li>Vykonávať reverse engineering alebo dekompiláciu</li>
                <li>Automatizovane sťahovať obsah (scraping, crawling) bez písomného súhlasu</li>
                <li>Používať logo TRČ alebo ochrannú známku CMEP na komerčné účely</li>
                <li>Vytvárať odvodené diela bez písomného súhlasu</li>
                <li>Obchádzať bezpečnostné opatrenia alebo autorizačné mechanizmy</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>4. Obsah vložený používateľmi</h2>
              <p>
                Používateľ si <strong style={{ color: FG }}>zachováva autorské práva</strong> k obsahu, ktorý sám vloží
                (texty inzerátov, fotografie materiálov, popisy). Vložením obsahu do platformy udeľuje
                prevádzkovateľovi <strong style={{ color: FG }}>bezplatnú, nevýhradnú licenciu</strong> na:
              </p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li>Zobrazenie obsahu v rámci platformy</li>
                <li>Uloženie obsahu v databáze</li>
                <li>Zasielanie notifikácií súvisiacich s obsahom</li>
              </ul>
              <p className="mt-3">
                Táto licencia zaniká v momente, keď používateľ obsah vymaže alebo vymaže svoj účet,
                okrem záloh uchovávaných po dobu max. 30 dní.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>5. Ochrana duševného vlastníctva</h2>
              <p>
                Akékoľvek neoprávnené použitie platformy, jej častí alebo loga môže byť postihnuté
                podľa <strong style={{ color: FG }}>zákona č. 185/2015 Z. z. (Autorský zákon)</strong> a
                <strong style={{ color: FG }}> zákona č. 513/1991 Zb. (Obchodný zákonník)</strong>.
              </p>
              <p className="mt-3">
                Prevádzkovateľ si vyhradzuje právo uplatniť náhradu škody a ušlý zisk v prípade porušenia tejto licencie.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>6. Použité open-source technológie</h2>
              <p>Platforma je postavená na open-source technológiách. Ich používanie sa riadi vlastnými licenciami:</p>
              <ul className="mt-3 list-disc space-y-1 pl-6">
                <li><strong style={{ color: FG }}>Next.js</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>React</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>FastAPI</strong> — MIT License</li>
                <li><strong style={{ color: FG }}>PostgreSQL</strong> — PostgreSQL License</li>
                <li><strong style={{ color: FG }}>Redis / Valkey</strong> — BSD-3-Clause</li>
                <li><strong style={{ color: FG }}>Tailwind CSS</strong> — MIT License</li>
              </ul>
              <p className="mt-3">
                Táto licencia sa <strong style={{ color: FG }}>nevzťahuje</strong> na tieto open-source komponenty.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>7. Použitie fotografií a obrázkov</h2>
              <p>
                Fotografie materiálov zobrazené na landing stránke sú licencované z <strong style={{ color: FG }}>Unsplash</strong>
                (Unsplash License) alebo sú vlastníctvom prevádzkovateľa. Fotografie vložené používateľmi
                sú výhradne v zodpovednosti používateľa, ktorý ich vložil.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>8. Ukončenie licencie</h2>
              <p>
                Prevádzkovateľ môže túto licenciu <strong style={{ color: FG }}>okamžite ukončiť</strong> v prípade
                porušenia podmienok (najmä bod 3 a 5). Po ukončení licencie je používateľ povinný
                okamžite prestať používať platformu a vymazať všetky prípadné kópie.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>9. Rozhodné právo</h2>
              <p>
                Táto licencia sa riadi právom <strong style={{ color: FG }}>Slovenskej republiky</strong>.
                Na riešenie sporov je príslušný súd v sídle prevádzkovateľa.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>10. Kontakt pre právne otázky</h2>
              <p>V prípade otázok týkajúcich sa licencie, autorských práv alebo porušenia práv kontaktujte:</p>
              <ul className="mt-3 space-y-1">
                <li>E-mail: <a href="mailto:trc-cmep@gmail.com" style={{ color: GOLD_BRIGHT }}>trc-cmep@gmail.com</a></li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-xl" style={{ color: FG, fontFamily: 'Fraunces, serif' }}>11. Záverečné ustanovenia</h2>
              <p>
                Táto licencia je platná od {today} a nahrádza všetky predchádzajúce licenčné podmienky.
                Prevádzkovateľ si vyhradzuje právo ju jednostranne meniť; o zmenách budú používatelia
                informovaní e-mailom alebo notifikáciou v platforme.
              </p>
              <p className="mt-3">
                Používaním platformy CMEP používateľ vyjadruje súhlas s touto licenciou v plnom rozsahu.
              </p>
            </section>

            <p className="pt-8 text-sm" style={{ color: FAINT }}>
              © {year} Radoslav Čornanič · TRČ · Všetky práva vyhradené.
            </p>

            <div className="mt-10 flex flex-wrap gap-4 text-sm">
              <Link href="/terms" style={{ color: GOLD_BRIGHT }}>Obchodné podmienky →</Link>
              <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>Ochrana osobných údajov →</Link>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
