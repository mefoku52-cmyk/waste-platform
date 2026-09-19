'use client';

import Link from 'next/link';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';

const FAQ = [
  {
    q: 'Čo je CMEP?',
    a: 'CMEP (Circular Materials Exchange Platform) je B2B burza pre obehové materiály. Firmy tu medzi sebou predávajú a vymieňajú druhotné suroviny, prebytky z výroby a vedľajšie produkty.',
  },
  {
    q: 'Pre koho je platforma určená?',
    a: 'Pre firmy, ktoré majú prebytočný materiál (drevo, kov, papier, plasty, bioodpad) a pre firmy, ktoré tento materiál hľadajú ako vstup do svojej výroby.',
  },
  {
    q: 'Ako overujete firmy?',
    a: 'Každá firma, ktorá sa chce zapojiť do obchodovania, musí prejsť overením IČO. Overenie zabezpečuje, že na platforme sú len seriózne firmy.',
  },
  {
    q: 'Sú kontakty viditeľné?',
    a: 'Kontakty (telefón, e-mail) zostávajú skryté, kým sa firmy nedohodnú. Komunikácia prebieha cez interný chat platformy.',
  },
  {
    q: 'Kolik stojí používanie?',
    a: 'Registrácia a základné používanie platformy sú zdarma. Prémiové funkcie (priorita v zozname, neobmedzené inzeráty, API prístup) budú spoplatnené.',
  },
  {
    q: 'Ako začnem?',
    a: 'Zaregistrujte sa, vytvorte firmu, pridajte prvú ponuku. Ostatné firmy vás kontaktujú priamo cez platformu.',
  },
];

export default function AboutPage() {
  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <div className="min-h-screen" style={{ background: BG, color: FG, fontFamily: 'Outfit, sans-serif' }}>
        <header
          className="border-b"
          style={{ borderColor: 'color-mix(in srgb, #c9a84c 20%, transparent)' }}
        >
          <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-4">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="TRČ" className="h-10 w-10 rounded-full object-cover" />
              <span style={{ fontFamily: 'Fraunces, serif', fontSize: '1.25rem' }}>CMEP</span>
            </Link>
            <div className="ml-auto flex gap-4 text-sm">
              <Link href="/" style={{ color: MUTED }}>Domov</Link>
              <Link href="/login" style={{ color: MUTED }}>Prihlásiť</Link>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-4xl px-4 py-16">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
            O PROJEKTE
          </p>
          <h1 className="mb-6 text-4xl leading-tight md:text-5xl" style={{ fontFamily: 'Fraunces, serif' }}>
            Súkromná burza pre obehové materiály
          </h1>
          <p className="mb-12 text-base leading-relaxed" style={{ color: MUTED }}>
            CMEP vznikol v Žiline s jednou myšlienkou: <em style={{ color: GOLD_BRIGHT }}>odpad je len materiál, ktorý ešte nenašiel kupca.</em>{' '}
            Prepájame firmy, ktoré majú prebytky, s firmami, ktoré ich vedia využiť. Bez aukčného cirkusu, bez zbytočných telefonátov,
            cez jeden prehľadný digitálny systém.
          </p>

          {/* O FIRME */}
          <section className="mb-12">
            <h2 className="mb-4 text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>O firme</h2>
            <div className="space-y-3 text-base" style={{ color: MUTED }}>
              <p>
                <strong style={{ color: FG }}>Prevádzkovateľ:</strong> Radoslav Čornanič
              </p>
              <p>
                <strong style={{ color: FG }}>Sídlo:</strong> Ulič 63, 067 67 Ulič, Slovenská republika
              </p>
              <p>
                <strong style={{ color: FG }}>IČO:</strong> 51745666
              </p>
              <p>
                <strong style={{ color: FG }}>Zameranie:</strong> Digitálne riešenia pre obehové hospodárstvo
              </p>
            </div>
          </section>

          {/* KONTAKT */}
          <section className="mb-12">
            <h2 className="mb-4 text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>Kontakt</h2>
            <div className="space-y-3 text-base" style={{ color: MUTED }}>
              <p>
                <strong style={{ color: FG }}>E-mail:</strong>{' '}
                <a href="mailto:orlovic1611@gmail.com" style={{ color: GOLD_BRIGHT }}>
                  orlovic1611@gmail.com
                </a>
              </p>
              <p>
                <strong style={{ color: FG }}>Telefón:</strong>{' '}
                <a href="tel:+421910617338" style={{ color: GOLD_BRIGHT }}>
                  +421 910 617 338
                </a>
              </p>
              <p>
                <strong style={{ color: FG }}>Pošta:</strong> Ulič 63, 067 67 Ulič, Slovenská republika
              </p>
            </div>
          </section>

          {/* FAQ */}
          <section className="mb-12">
            <h2 className="mb-6 text-2xl" style={{ fontFamily: 'Fraunces, serif' }}>
              Často kladené otázky
            </h2>
            <div className="space-y-3">
              {FAQ.map((item) => (
                <details
                  key={item.q}
                  className="rounded-2xl border p-5 transition-colors"
                  style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}
                >
                  <summary
                    className="cursor-pointer text-lg"
                    style={{ fontFamily: 'Fraunces, serif', color: GOLD_BRIGHT }}
                  >
                    {item.q}
                  </summary>
                  <p className="mt-3 text-sm leading-relaxed" style={{ color: MUTED }}>
                    {item.a}
                  </p>
                </details>
              ))}
            </div>
          </section>

          {/* PRÁVNE */}
          <section className="border-t pt-8" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)' }}>
            <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>
              PRÁVNE
            </p>
            <div className="flex flex-wrap gap-4 text-sm">
              <Link href="/terms" style={{ color: GOLD_BRIGHT }}>Obchodné podmienky</Link>
              <Link href="/privacy" style={{ color: GOLD_BRIGHT }}>Ochrana údajov</Link>
              <Link href="/license" style={{ color: GOLD_BRIGHT }}>Licencia</Link>
            </div>
          </section>

          <p className="mt-12 text-xs" style={{ color: FAINT }}>
            © {new Date().getFullYear()} Radoslav Čornanič · TRČ · Všetky práva vyhradené.
          </p>
        </main>
      </div>
    </>
  );
}
