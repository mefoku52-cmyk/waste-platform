'use client';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useT } from '@/lib/i18n/context';
import { useCurrentUser } from '@/features/auth/hooks/use-current-user';

const GOLD = '#d6a84f';
const GOLD_BRIGHT = '#f1d58a';
const BG = '#0b0d0f';
const FG = '#f5f7f8';
const MUTED = '#aeb5bb';
const FAINT = '#737b82';
// const DANGER = '#c45c4a';

const MATERIALS = [
  { key: 'drevo', label: 'Drevo', img: 'https://images.unsplash.com/photo-1542621334-a254cf47733d?w=1200&q=80', desc: 'Piliny, odrezky, palety. Kým ich niekto spáli, niekto iný ich hľadá na dosky.' },
  { key: 'kov', label: 'Kov', img: 'https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=1200&q=80', desc: 'Šrot, káble, konštrukcie, spony, obliny, odrezky. Kým z nich bude hrdza, niekto z nich vyrobí nové.' },
  { key: 'papier', label: 'Papier', img: 'https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=1200&q=80', desc: 'Regranulát, kartón, noviny. Pravidelný odber, nie jednorazový inzerát.' },
  { key: 'plasty', label: 'Plasty', img: 'https://images.unsplash.com/photo-1618363010061-a42f6e39e3d8?w=1200&q=80', desc: 'Regranulát, fólie, PET fľaše. Namiesto skládky nový život v priemysle.' },
  { key: 'bioodpad', label: 'Bioodpad', img: 'https://images.unsplash.com/photo-1611843467160-25afb8df1074?w=1200&q=80', desc: 'Kompost, štiepka, organické zvyšky. Z pôdy vzniká, do pôdy sa vracia.' },
];

const STEPS = [
  { n: '01', icon: '◐', titleKey: 'landing.steps.1.title', textKey: 'landing.steps.1.text' },
  { n: '02', icon: '◇', titleKey: 'landing.steps.2.title', textKey: 'landing.steps.2.text' },
  { n: '03', icon: '◆', titleKey: 'landing.steps.3.title', textKey: 'landing.steps.3.text' },
];

export default function LandingPage() {
  const { t } = useT();
  const router = useRouter();
  const { data: me, isLoading: meLoading } = useCurrentUser();
  const [menuOpen, setMenuOpen] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' });
  const [sent, setSent] = useState(false);

  // Ak je používateľ prihlásený, landing nemá zmysel — pošli ho na dashboard.
  // Neprihlásených necháme na landing.
  useEffect(() => {
    if (!meLoading && me && (me as any).id) {
      router.replace('/dashboard');
    }
  }, [me, meLoading, router]);

  const onContact = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <style jsx global>{`
        body { background: ${BG}; color: ${FG}; font-family: 'Outfit', system-ui, sans-serif; }
        .ff { font-family: 'DM Serif Display', 'Times New Roman', serif; }
        .grad { background-image: linear-gradient(to top, rgba(11,13,15,0.96) 0%, rgba(11,13,15,0.68) 42%, rgba(11,13,15,0.18) 76%, transparent 100%); }
      `}</style>

      <div className="min-h-screen" style={{ background: BG, color: FG }}>
        {/* HEADER */}
        <header
          className="sticky top-0 z-40 border-b backdrop-blur-md"
          style={{
            borderColor: 'rgba(255,255,255,0.08)',
            background: 'rgba(11,13,15,0.92)',
          }}
        >
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
            <Link href="/" className="flex min-w-0 items-center gap-3">
              <img
                src="/trc-mark.jpg"
                alt="CMEP"
                className="h-10 w-10 shrink-0 rounded-full object-cover"
              />
              <div className="min-w-0 hidden sm:block">
                <p
                  className="truncate text-[10px] font-medium uppercase tracking-[0.2em]"
                  style={{ color: GOLD }}
                >
                  {t('landing.brandKicker')}
                </p>
                <p className="ff truncate text-lg leading-none" style={{ color: FG }}>
                  {t('landing.materials')}
                </p>
              </div>
            </Link>
            <nav className="hidden items-center gap-2 md:flex">
              <Link href="/login" className="rounded-md border px-4 py-2 text-sm" style={{ borderColor: 'rgba(255,255,255,0.14)', color: FG }}>
                {t('landing.login')}
              </Link>
              <Link href="/register" className="rounded-md px-4 py-2 text-sm font-medium" style={{ background: GOLD, color: BG }}>
                {t('landing.postListing')}
              </Link>
            </nav>
            <button onClick={() => setMenuOpen((v) => !v)} className="rounded-md border px-3 py-2 text-sm md:hidden" style={{ borderColor: 'rgba(255,255,255,0.14)' }}>
              ☰
            </button>
          </div>
          {menuOpen && (
            <div
              className="border-t px-4 py-3 md:hidden"
              style={{ borderColor: 'rgba(255,255,255,0.08)' }}
            >
              <Link href="/login" className="block py-2 text-sm">{t('landing.login')}</Link>
              <Link href="/register" className="block py-2 text-sm" style={{ color: GOLD_BRIGHT }}>{t('landing.postListing')}</Link>
              <Link href="/dashboard" className="block py-2 text-sm">{t('landing.dashboard')}</Link>
            </div>
          )}
        </header>

        {/* HERO */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0" style={{
              background:
                'radial-gradient(circle at 30% 20%, rgba(214,168,79,0.07), transparent 58%)',
            }} />
          <div className="relative mx-auto max-w-6xl px-4 py-12 md:py-20">
            <div className="px-1 py-4 md:px-2 md:py-8">
              <p className="mb-3 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>
                {t('landing.heroKicker')}
              </p>
              <h1 className="ff text-4xl font-normal leading-[1.05] tracking-[-0.02em] md:text-6xl">
                TRČ · CMEP
              </h1>
              <p className="ff mt-4 text-2xl italic leading-snug md:text-3xl" style={{ color: GOLD_BRIGHT }}>
                {t('landing.heroSlogan')}
              </p>
              <p className="mt-3 text-base md:text-lg" style={{ color: GOLD_BRIGHT }}>
                {t('landing.heroSubtitle')}
              </p>
              <p className="mt-4 max-w-2xl text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
                {t('landing.heroDesc')}
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/register" className="rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
                  {t('landing.heroCtaAdd')}
                </Link>
                <Link href="#trh" className="rounded-md border px-6 py-3 text-sm" style={{ borderColor: 'rgba(214,168,79,0.55)', color: FG }}>
                  {t('landing.heroCtaMarket')}
                </Link>
              </div>

              
            </div>

            <div className="mt-12 flex justify-center">
              <img src="/trc-logo.jpg" alt="RC" className="max-w-md w-full opacity-90" />
            </div>
          </div>
        </section>

        {/* PREČO CMEP */}
        <section className="border-t border-white/10">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.whyKicker')}</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              CMEP — Circular Materials Exchange Platform.
            </h2>

            <div className="mt-8 max-w-3xl space-y-5 text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              <p>
                {t('landing.whyP1')} <strong style={{ color: FG }}>{t('landing.whyP1Bold')}</strong>
              </p>
              <p>
                <strong style={{ color: FG }}>{t('landing.whyP2Bold')}</strong>
                {t('landing.whyP2Rest')}
              </p>
            </div>

            {/* TRI PILIERE */}
            <div className="mt-10 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border p-6" style={{ borderColor: 'rgba(255,255,255,0.10)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>{t('landing.forCompanies')}</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {t('landing.forCompaniesDesc')}
                </p>
              </div>
              <div className="rounded-2xl border p-6" style={{ borderColor: 'rgba(255,255,255,0.10)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>{t('landing.forPeople')}</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {t('landing.forPeopleDesc')}
                </p>
              </div>
              <div className="rounded-2xl border p-6" style={{ borderColor: 'rgba(255,255,255,0.10)' }}>
                <p className="ff mb-2 text-2xl" style={{ color: GOLD_BRIGHT }}>{t('landing.forPlanet')}</p>
                <p className="text-sm leading-relaxed" style={{ color: MUTED }}>
                  {t('landing.forPlanetDesc')}
                </p>
              </div>
            </div>

            <p className="ff mt-10 text-2xl italic leading-tight md:text-3xl" style={{ color: GOLD_BRIGHT }}>
              {t('landing.whyFooter')}
            </p>
          </div>
        </section>

        {/* ČO SA TU HÝBE */}
        <section id="trh" className="border-t border-white/10">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.flowsKicker')}</p>
            <h2 className="ff mb-8 text-2xl leading-snug md:text-3xl">{t('landing.flowsTitle')}</h2>
            <div className="flex flex-col gap-5">
              {MATERIALS.map((m) => (
                <Link key={m.key} href={`/dashboard?cat=${m.key}`} className="group relative block overflow-hidden rounded-2xl border border-white/10">
                  <div className="relative aspect-[21/9] w-full">
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
        <section className="border-t border-white/10">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.lossKicker')}</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              {t('landing.lossTitle')}
            </h2>
            <p className="mt-6 max-w-2xl text-base leading-relaxed" style={{ color: MUTED }}>
              {t('landing.lossDesc')}
            </p>
            <Link href="/dashboard" className="mt-8 inline-block rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
              {t('landing.lossCta')}
            </Link>
          </div>
        </section>

        {/* AKO TO FUNGUJE */}
        <section className="border-t border-white/10">
          <div className="mx-auto max-w-6xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.howKicker')}</p>
            <h2 className="ff mb-8 text-2xl leading-snug md:text-3xl">{t('landing.stepsTitle')}</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {STEPS.map((s) => (
                <div key={s.n} className="rounded-2xl border p-6 md:p-8" style={{ borderColor: 'rgba(255,255,255,0.10)' }}>
                  <p className="ff text-5xl" style={{ color: 'rgba(214,168,79,0.42)' }}>{s.n}</p>
                  <p className="mt-4 text-2xl" style={{ color: GOLD }}>{s.icon}</p>
                  <p className="ff mt-3 text-2xl">{t(s.titleKey)}</p>
                  <p className="mt-2 text-sm leading-relaxed" style={{ color: MUTED }}>{t(s.textKey)}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ZHODA / KONTAKT PRÍDE AKO SPRÁVA */}
        <section className="border-t border-white/10">
          <div className="mx-auto max-w-3xl px-4 py-16 md:py-20 text-center">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.privacyKicker')}</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">
              {t('landing.privacyTitle')}
            </h2>
            <p className="mt-6 text-base leading-relaxed md:text-lg" style={{ color: MUTED }}>
              {t('landing.privacyDesc')}
            </p>
          </div>
        </section>

        {/* TICHÝ VSTUP */}
        <section className="border-t border-white/10">
          <div className="mx-auto max-w-3xl px-4 py-16 md:py-20">
            <p className="mb-4 text-[11px] uppercase tracking-[0.3em]" style={{ color: GOLD }}>{t('landing.contactKicker')}</p>
            <h2 className="ff text-4xl leading-tight md:text-5xl">{t('landing.contactTitle')}</h2>
            <p className="mt-6 text-base" style={{ color: MUTED }}>
              {t('landing.contactDesc')}
            </p>
            {sent ? (
              <div className="mt-8 rounded-2xl border p-6" style={{ borderColor: 'rgba(255,255,255,0.14)', background: 'rgba(255,255,255,0.035)' }}>
                <p className="ff text-xl" style={{ color: GOLD_BRIGHT }}>{t('landing.thanksTitle')}</p>
                <p className="mt-2 text-sm" style={{ color: MUTED }}>{t('landing.thanksDesc')}</p>
              </div>
            ) : (
              <form onSubmit={onContact} className="mt-8 grid gap-3">
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder={t('landing.phName')} className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'rgba(255,255,255,0.12)', color: FG }} />
                <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder={t('landing.phEmail')} className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'rgba(255,255,255,0.12)', color: FG }} />
                <input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} placeholder={t('landing.phCompany')} className="h-12 rounded-md border bg-transparent px-4 outline-none" style={{ borderColor: 'rgba(255,255,255,0.12)', color: FG }} />
                <textarea required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder={t('landing.phMessage')} rows={5} className="rounded-md border bg-transparent px-4 py-3 outline-none" style={{ borderColor: 'rgba(255,255,255,0.12)', color: FG }} />
                <button type="submit" className="justify-self-start rounded-md px-6 py-3 text-sm font-semibold" style={{ background: GOLD, color: BG }}>
                  {t('landing.send')}
                </button>
              </form>
            )}
          </div>
        </section>

        {/* FOOTER */}
        <footer className="border-t border-white/10">
          <div className="mx-auto max-w-6xl px-4 py-12">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <img src="/trc-mark.jpg" alt="CMEP" className="h-12 w-12 rounded-full object-cover" />
                <div>
                  <p className="ff text-2xl">CMEP</p>
                  <p className="text-xs" style={{ color: MUTED }}>Circular Materials Exchange Platform</p>
                </div>
              </div>
              <p className="text-sm" style={{ color: MUTED }}>{t('landing.footerTagline')}</p>
            </div>
            <div className="mt-8 grid grid-cols-2 gap-6">
              <div>
                <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>{t('footer.marketSection')}</p>
                <Link href="/dashboard" className="block py-1 text-sm" style={{ color: FG }}>{t('landing.marketplace')}</Link>
                <Link href="/dashboard" className="block py-1 text-sm" style={{ color: FG }}>{t('landing.companies')}</Link>
                <Link href="#preco" className="block py-1 text-sm" style={{ color: FG }}>{t('landing.about')}</Link>
              </div>
              <div>
                <p className="mb-3 text-[10px] uppercase tracking-[0.25em]" style={{ color: GOLD }}>{t('footer.trust')}</p>
                <span className="block py-1 text-sm" style={{ color: FG }}>{t('footer.verifiedIco')}</span>
                <span className="block py-1 text-sm" style={{ color: FG }}>{t('landing.hiddenContacts')}</span>
                <span className="block py-1 text-sm" style={{ color: FG }}>{t('landing.privateExchange')}</span>
              </div>
            </div>
            <div className="mt-10 flex items-center justify-between border-t pt-6 text-xs" style={{ borderColor: 'rgba(255,255,255,0.08)', color: FAINT }}>
              <span>© CMEP · Circular Materials Exchange Platform · Slovensko</span>
              <span>{t('footer.langLabel')}: SK</span>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
