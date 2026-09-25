'use client';
import Link from 'next/link';
import { useState } from 'react';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';
const FAINT = '#6e6658';
const DANGER = '#c45c4a';

const MATERIALS = [
  { key: 'drevo', label: 'Drevo', img: 'https://images.unsplash.com/photo-1542621334-a254cf47733d?w=1200&q=80', desc: 'Piliny, odrezky, palety. Kým ich niekto spáli, niekto iný ich hľadá na dosky.' },
  { key: 'kov', label: 'Kov', img: 'https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=1200&q=80', desc: 'Šrot, káble, konštrukcie, spony, obliny, odrezky. Kým z nich bude hrdza, niekto z nich vyrobí nové.' },
  { key: 'papier', label: 'Papier', img: 'https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=1200&q=80', desc: 'Regranulát, kartón, noviny. Pravidelný odber, nie jednorazový inzerát.' },
  { key: 'plasty', label: 'Plasty', img: 'https://images.unsplash.com/photo-1618363010061-a42f6e39e3d8?w=1200&q=80', desc: 'Regranulát, fólie, PET fľaše. Namiesto skládky nový život v priemysle.' },
  { key: 'bioodpad', label: 'Bioodpad', img: 'https://images.unsplash.com/photo-1611843467160-25afb8df1074?w=1200&q=80', desc: 'Kompost, štiepka, organické zvyšky. Z pôdy vzniká, do pôdy sa vracia.' },
];

const STEPS = [
  { n: '01', icon: '◐', title: 'Zverejnite', text: 'Materiál, lokalita, tonáž. Cenu môžete nechať na dohodu. Deväťdesiat sekúnd, nie tendrový spis.' },
  { n: '02', icon: '◇', title: 'Ozveme sa', text: 'Firmy, ktoré hľadajú presne to, čo ponúkate, vás kontaktujú cez interný chat. Žiadne telefonáty, žiadne e-maily, žiadny spam.' },
  { n: '03', icon: '◆', title: 'Dohodnite', text: 'Cena, doprava, termín — všetko v chate. Bez papierovačiek, bez aukčného cirkusu, bez zbytočných krokov.' },
];

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' });
  const [sent, setSent] = useState(false);

  const onContact = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400;1,9..144,500&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <style jsx global>{`
        body { background: ${BG}; color: ${FG}; font-family: 'Outfit', system-ui, sans-serif; }
        .ff { font-family: 'Fraunces', 'Times New Roman', serif; }
        .grad { background-image: linear-gradient(to top, rgba(9,8,7,0.95) 0%, rgba(9,8,7,0.6) 40%, rgba(9,8,7,0.15) 75%, transparent 100%); }
      `}</style>

      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        {/* HEADER */}
        <header className="sticky top-0 z-40 border-b border-[color:color-mix(in_srgb,#c9a84c_20%,transparent)] backdrop-blur-md" style={{ background: 'rgba(9,8,7,0.85)' }}>
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
            <Link href="/" className="flex items-center gap-3">
              <img src="/trc-mark.jpg" alt="CMEP" className="h-10 w-10 rounded-full object-cover" />
              <div className="hidden sm:block">
                <p className="text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>CMEP · BURZA OBEHOVÝCH MATERIÁLOV</p>
                <p className="ff text-lg leading-none">Obehové materiály</p>
              </div>
            </Link>
            <nav className="hidden items-center gap-2 md:flex">
              <Link href="/login" className="rounded-md border px-4 py-2 text-sm" style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', color: FG }}>
                Prihlásiť sa
              </Link>
              <Link href="/register" className="rounded-md px-4 py-2 text-sm font-medium" style={{ background: GOLD, color: BG }}>
                Zverejniť
              </Link>
            </nav>
            <button onClick={() => setMenuOpen((v) => !v)} className="rounded-md border px-3 py-2 text-sm md:hidden" style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)' }}>
              ☰
            </button>
          </div>
          {menuOpen && (
            <div className="border-t border-[color:color-mix(in_srgb,#c9a84c_20%,transparent)] px-4 py-3 md:hidden">
              <Link href="/login" className="block py-2 text-sm">Prihlásiť sa</Link>
              <Link href="/register" className="block py-2 text-sm" style={{ color: GOLD_BRIGHT }}>Zverejniť ponuku</Link>
              <Link href="/dashboard" className="block py-2 text-sm">Dashboard</Link>
            </div>
          )}
        </header>

        {/* HERO */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0" style={{ background: `radial-gradient(circle at 30% 20%, color-mix(in srgb, #c9a84c 8%, transparent), transparent 60%)` }} />
          <div className="relative mx-auto max-w-6xl px-4 py-16 md:py-24">
            <p className="mb-6 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
              SLOVENSKO · STREDNÁ EURÓPA · SÚKROMNÁ BURZA
            </p>
            <h1 className="ff text-5xl font-normal leading-[1.05] tracking-[-0.02em] md:text-7xl">
              Prebytok nie je odpad.
              <br />
              <em className="italic" style={{ color: GOLD_BRIGHT }}>
                Odpad je len materiál, ktorý ešte nenašiel svojho kupca. Materiál je hodnota, ktorá ešte nenašla svoj trh. A trh je miesto, kde sa z hodnoty stáva obchod. TRČ je to miesto.
              </em>
            </h1>
            <p className="mt-8 max-w-2xl text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              Firmy hádžu do kontajnera to, čo iné firmy hľadajú. Drevo. Kov. Papier. Plasty. Bioodpad.
              CMEP je tichá burza, kde sa z toho stane obchod — overené IČO, skryté kontakty, bez aukčného cirkusu.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link href="/register" className="rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
                Pridať / zverejniť ponuku
              </Link>
              <Link href="#trh" className="rounded-md border px-6 py-3 text-sm" style={{ borderColor: 'color-mix(in srgb, #c9a84c 45%, transparent)', color: FG }}>
                Pozrieť živý trh
              </Link>
            </div>

            {/* STATS */}
            <div className="mt-16 grid grid-cols-2 gap-6 md:grid-cols-4">
              {[
                { v: '447,6', l: 'TON NA TRHU' },
                { v: '8', l: 'OVERENÝCH FIRIEM' },
                { v: '10', l: 'ŽIVÝCH PONÚK', dot: true },
              ].map((s) => (
                <div key={s.l}>
                  <p className="ff text-4xl md:text-5xl" style={{ color: GOLD_BRIGHT }}>
                    {s.dot ? <span className="mr-2 inline-block h-2 w-2 rounded-full align-middle" style={{ background: '#6ee7a7' }} /> : null}
                    {s.v}
                  </p>
                  <p className="mt-1 text-[10px] uppercase tracking-[0.2em]" style={{ color: FAINT }}>{s.l}</p>
                </div>
              ))}
            </div>

            <div className="mt-16 flex justify-center">
              <img src="/trc-logo.jpg" alt="RC" className="max-w-md w-full opacity-90" />
            </div>
          </div>
        </section>

        {/* PRÁVE TERAZ */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PRÁVE TERAZ</p>
            <h2 className="ff mb-8 text-2xl leading-snug md:text-3xl">Materiál, ktorý ešte čaká na svojho kupca.</h2>
            <Link href="/dashboard" className="group relative block overflow-hidden rounded-2xl border border-[color:color-mix(in_srgb,#c9a84c_25%,transparent)]">
              <span
                className="absolute right-4 top-4 z-10 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.25em]"
                style={{ borderColor: GOLD, color: GOLD_BRIGHT, background: 'rgba(9,8,7,0.85)' }}
              >
                VZOR · takto vyzerá reálna ponuka
              </span>
              <div className="relative aspect-[16/9] w-full">
                <img src="https://images.unsplash.com/photo-1542621334-a254cf47733d?w=1600&q=80" alt="Piloviny" className="h-full w-full object-cover opacity-70 transition group-hover:opacity-90" />
                <div className="grad absolute inset-0" />
                <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8">
                  <p className="mb-3 text-[10px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>DNES NA STOLE</p>
                  <p className="ff text-3xl md:text-4xl" style={{ color: GOLD_BRIGHT }}>Piloviny</p>
                  <p className="mt-2 text-sm md:text-base" style={{ color: FG }}>Mám na ponuku predaj pilovín, asi 300 t.</p>
                  <p className="mt-3 text-xs" style={{ color: MUTED }}>Žilina · Drevo · 300 t</p>
                </div>
              </div>
            </Link>
          </div>
        </section>

        {/* PREČO CMEP */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>PREČO CMEP</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              CMEP — Circular Materials Exchange Platform.
            </h2>

            <div className="mt-8 max-w-3xl space-y-5 text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              <p>
                Svet produkuje viac odpadu, než dokáže spracovať. Firmy platia za likvidáciu
                materiálu, ktorý by iný dokázal využiť. <strong style={{ color: FG }}>My to meníme.</strong>
              </p>
              <p>
                <strong style={{ color: FG }}>CMEP prepája firmy, ktoré majú prebytky, s tými, ktoré ich potrebujú.</strong>
                Bez prostredníka. Bez zbytočných nákladov. Bez dopadu na planétu.
              </p>
            </div>

            {/* TRI PILIERE */}
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>Pre firmy</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  Nižšie náklady, nové príjmy, jednoduchšie hľadanie surovín.
                </p>
              </div>
              <div className="rounded-2xl border p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>Pre ľudí</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  Čistejšie prostredie, menej skládok, lepšia budúcnosť.
                </p>
              </div>
              <div className="rounded-2xl border p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>Pre planétu</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  Menej odpadu, viac obehu, viac času.
                </p>
              </div>
            </div>

            <p className="ff mt-10 text-2xl italic leading-tight md:text-3xl" style={{ color: GOLD_BRIGHT }}>
              CMEP — pretože čistota nie je luxus. Je to zodpovednosť.
            </p>
          </div>
        </section>

        {/* ČO SA TU HÝBE */}
        <section id="trh" className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>ČO SA TU HÝBE</p>
            <h2 className="ff mb-8 text-2xl leading-snug md:text-3xl">Päť prúdov. Jeden trh. Nekonečné možnosti.</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {MATERIALS.map((m) => (
                <Link key={m.key} href={`/dashboard?cat=${m.key}`} className="group relative block overflow-hidden rounded-2xl border border-[color:color-mix(in_srgb,#c9a84c_20%,transparent)]">
                  <div className="relative aspect-[16/10] w-full">
                    <img src={m.img} alt={m.label} className="h-full w-full object-cover opacity-60 transition group-hover:opacity-80 group-hover:scale-[1.02]" />
                    <div className="grad absolute inset-0" />
                    <div className="absolute bottom-0 left-0 right-0 p-6">
                      <p className="ff text-3xl" style={{ color: GOLD_BRIGHT }}>{m.label}</p>
                      <p className="mt-1 text-sm" style={{ color: MUTED }}>{m.desc}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* STRATA */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>STRATA, KTORÚ UŽ POČÍTATE</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              Každá tona na skládke je peniaz, o ktorý ste prišli.
            </h2>
            <p className="ff mt-6 text-3xl italic md:text-4xl" style={{ color: GOLD_BRIGHT }}>
              300 t pilín. Žilina. Dnes.
            </p>
            <p className="mt-6 max-w-2xl text-base leading-relaxed" style={{ color: MUTED }}>
              Piliny v Žiline. 300 t. Dnes. Kým dočítate túto vetu, niekto ich kúpi — alebo skončia v kotli.
              Burza existuje preto, aby sa to nestalo zo zotrvačnosti.
            </p>
            <Link href="/dashboard" className="mt-8 inline-block rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
              Do tržnice
            </Link>
          </div>
        </section>

        {/* AKO TO FUNGUJE */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>AKO TO FUNGUJE</p>
            <h2 className="ff mb-8 text-2xl leading-snug md:text-3xl">Tri kroky. Od prebytku k obchodu za pár minút.</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {STEPS.map((s) => (
                <div key={s.n} className="rounded-2xl border p-6 md:p-8" style={{ borderColor: 'color-mix(in srgb, #c9a84c 25%, transparent)' }}>
                  <p className="ff text-5xl" style={{ color: 'color-mix(in srgb, #c9a84c 60%, transparent)' }}>{s.n}</p>
                  <p className="mt-4 text-2xl" style={{ color: GOLD }}>{s.icon}</p>
                  <p className="ff mt-3 text-2xl">{s.title}</p>
                  <p className="mt-2 text-sm leading-relaxed" style={{ color: MUTED }}>{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ZHODA / KONTAKT PRÍDE AKO SPRÁVA */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-3xl px-4 py-16 md:py-20 text-center">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>SÚKROMIE</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              Kontakt príde ako správa.
            </h2>
            <p className="mt-6 text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              Telefón a e-mail ostanú skryté, kým sa firmy nedohodnú.
              Žiadny spam, žiadne obvolávanie. Súkromie je súčasť ceny.
            </p>
          </div>
        </section>

        {/* TICHÝ VSTUP */}
        <section className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-3xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>TICHÝ VSTUP</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">Nemusíte sa registrovať, aby ste sa opýtali.</h2>
            <p className="mt-6 text-base" style={{ color: MUTED }}>
              Jedna správa stačí. Ozveme sa ako firma firme — nie ako newsletter.
            </p>
            {sent ? (
              <div className="mt-8 rounded-2xl border p-6" style={{ borderColor: 'color-mix(in srgb, #c9a84c 35%, transparent)', background: 'rgba(201,168,76,0.05)' }}>
                <p className="ff text-xl" style={{ color: GOLD_BRIGHT }}>Ďakujeme. Ozveme sa.</p>
                <p className="mt-2 text-sm" style={{ color: MUTED }}>Vaša správa je u nás. Odpovieme do 24 hodín.</p>
              </div>
            ) : (
              <form onSubmit={onContact} className="mt-8 grid gap-3">
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Meno" className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }} />
                <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="E-mail" className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }} />
                <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder="Firma" className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }} />
                <textarea required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="Správa" rows={5} className="rounded-md border bg-transparent px-4 py-3 outline-none" style={{ borderColor: 'color-mix(in srgb, #c9a84c 30%, transparent)', color: FG }} />
                <button type="submit" className="justify-self-start rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
                  Odoslať
                </button>
              </form>
            )}
          </div>
        </section>

        {/* FOOTER */}
        <footer className="border-t border-[color:color-mix(in_srgb,#c9a84c_15%,transparent)]">
          <div className="mx-auto max-w-6xl px-4 py-12">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <img src="/trc-mark.jpg" alt="CMEP" className="h-12 w-12 rounded-full object-cover" />
                <div>
                  <p className="ff text-2xl">CMEP</p>
                  <p className="text-xs" style={{ color: MUTED }}>Circular Materials Exchange Platform</p>
                </div>
              </div>
              <p className="text-sm" style={{ color: MUTED }}>Súkromná burza. Overené firmy. Kontakty, ktoré patria vám.</p>
            </div>
            <div className="mt-8 grid grid-cols-2 gap-6">
              <div>
                <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>TRH</p>
                <Link href="/dashboard" className="block py-1 text-sm" style={{ color: FG }}>Trhovisko</Link>
                <Link href="/dashboard" className="block py-1 text-sm" style={{ color: FG }}>Firmy</Link>
                <Link href="#preco" className="block py-1 text-sm" style={{ color: FG }}>O platforme</Link>
              </div>
              <div>
                <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>DÔVERA</p>
                <span className="block py-1 text-sm" style={{ color: FG }}>Overené IČO</span>
                <span className="block py-1 text-sm" style={{ color: FG }}>Skryté kontakty</span>
                <span className="block py-1 text-sm" style={{ color: FG }}>Súkromná burza</span>
              </div>
            </div>
            <div className="mt-10 flex items-center justify-between border-t pt-6 text-xs" style={{ borderColor: 'color-mix(in srgb, #c9a84c 15%, transparent)', color: FAINT }}>
              <span>© CMEP · Circular Materials Exchange Platform · Slovensko</span>
              <span>JAZYK: SK</span>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
