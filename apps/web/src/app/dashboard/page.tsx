'use client';

import Link from 'next/link';

import { AppShell } from '@/components/layout/app-shell';
import { useUnreadCount } from '@/features/chat';

const GOLD = '#c9a84c';
const GOLD_BRIGHT = '#e8d48b';
const MUTED = '#9a8f7c';
const SILVER = '#e5e5e5';
const SILVER_MUTED = '#a8a8a8';

// 6 navigačných dlaždíc — každá má vlastnú fotku a href.
const DASHBOARD_TILES = [
  {
    key: 'overview',
    href: '/dashboard',
    label: 'Prehľad',
    desc: 'Váš prehľad, aktivita a štatistiky',
    img: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1600&q=80',
  },
  {
    key: 'listings',
    href: '/dashboard/listings',
    label: 'Ponuky',
    desc: 'Trhovisko materiálov a moje ponuky',
    img: 'https://images.unsplash.com/photo-1553413077-190dd305871c?w=1600&q=80',
  },
  {
    key: 'companies',
    href: '/dashboard/companies',
    label: 'Firmy',
    desc: 'Firmy v sieti a moja firma',
    img: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&q=80',
  },
  {
    key: 'documents',
    href: '/dashboard/documents',
    label: 'Dokumenty',
    desc: 'Zmluvy, faktúry a prílohy',
    img: 'https://images.unsplash.com/photo-1568667256549-094345857637?w=1600&q=80',
  },
  {
    key: 'inquiries',
    href: '/dashboard/inquiries',
    label: 'Dopyt',
    desc: 'Dopyty a komunikácia s firmami',
    img: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=1600&q=80',
  },
  {
    key: 'chat',
    href: '/dashboard/chat',
    label: 'Chat',
    desc: 'Interné správy medzi firmami',
    img: 'https://images.unsplash.com/photo-1587560699334-cc4ff634909a?w=1600&q=80',
  },
] as const;

// 5 dekoratívnych materiálov — neklikateľné, len na vizuál pod dlaždicami.
const DASHBOARD_MATERIALS = [
  {
    key: 'drevo',
    label: 'Drevo',
    img: 'https://images.unsplash.com/photo-1542621334-a254cf47733d?w=400&q=80',
  },
  {
    key: 'kov',
    label: 'Kov',
    img: 'https://images.unsplash.com/photo-1567095761054-7a02e69e5c43?w=400&q=80',
  },
  {
    key: 'papier',
    label: 'Papier',
    img: 'https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=400&q=80',
  },
  {
    key: 'plasty',
    label: 'Plasty',
    img: 'https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=400&q=80',
  },
  {
    key: 'bioodpad',
    label: 'Bioodpad',
    img: 'https://images.unsplash.com/photo-1611843467160-25afb8df1074?w=400&q=80',
  },
] as const;

export default function DashboardPage() {
  const { data: unreadData } = useUnreadCount();
  const unreadChat = Number((unreadData as any)?.unread || 0);

  return (
    <AppShell>
      <div className="mx-auto w-full max-w-6xl px-4 py-7 pb-12 sm:px-6 sm:py-10">
        {/* ═══ VITAJTE — bez rámčeka, italic ═══ */}
        <section className="mb-12">
          <p
            className="mb-3 text-[11px] uppercase tracking-[0.3em] italic"
            style={{ color: GOLD }}
          >
            Vitajte na platforme
          </p>

          <h1
            className="mb-4 text-5xl italic leading-[1.05] tracking-[-0.02em] md:text-6xl"
            style={{ color: GOLD_BRIGHT, fontFamily: 'DM Serif Display, serif' }}
          >
            TRČ · CMEP
          </h1>

          <p
            className="max-w-2xl text-base italic leading-relaxed md:text-lg"
            style={{ color: MUTED }}
          >
            Súkromná burza pre obehové materiály. Overené firmy, skryté kontakty,
            žiadny spam. Filtruj, hľadaj, dohodni — všetko na jednom mieste.
          </p>

          <p
            className="mt-8 text-2xl italic leading-snug md:text-3xl"
            style={{ color: GOLD_BRIGHT, fontFamily: 'DM Serif Display, serif' }}
          >
            Menej odpadu. Viac obchodu.
          </p>

          <p
            className="mt-3 max-w-2xl text-base italic leading-relaxed md:text-lg"
            style={{ color: MUTED }}
          >
            Trhovisko firiem a obehových materiálov. Filtruj, hľadaj, dohodni.
          </p>
        </section>

        {/* ═══ 6 NAVIGAČNÝCH DLAŽDÍC (pod sebou, strieborné) ═══ */}
        <section className="mb-10 flex flex-col gap-3">
          {DASHBOARD_TILES.map((tile) => (
            <Link
              key={tile.key}
              href={tile.href}
              className="group relative block overflow-hidden rounded-2xl border transition-all hover:scale-[1.005]"
              style={{
                borderColor: 'rgba(192,192,192,0.25)',
                aspectRatio: '21/9',
              }}
            >
              <img
                src={tile.img}
                alt={tile.label}
                className="absolute inset-0 h-full w-full object-cover opacity-40 transition-opacity group-hover:opacity-60"
              />
              <div
                className="absolute inset-0"
                style={{
                  background:
                    'linear-gradient(to top, rgba(9,8,7,0.95) 0%, rgba(9,8,7,0.4) 50%, transparent 100%)',
                }}
              />
              <div className="absolute bottom-0 left-0 right-0 p-6 md:p-7">
                <p
                  className="text-3xl italic leading-tight md:text-4xl"
                  style={{
                    fontFamily: 'DM Serif Display, serif',
                    color: SILVER,
                  }}
                >
                  {tile.label}
                  {tile.key === 'chat' && unreadChat > 0 && (
                    <span
                      className="ml-3 inline-flex items-center justify-center rounded-full px-2 py-1 text-sm not-italic font-bold align-middle"
                      style={{ background: '#c45c4a', color: '#f3ead8' }}
                    >
                      {unreadChat}
                    </span>
                  )}
                </p>
                <p
                  className="mt-1 text-sm md:text-base"
                  style={{ color: SILVER_MUTED }}
                >
                  {tile.desc}
                </p>
              </div>
            </Link>
          ))}
        </section>

        {/* ═══ 5 DEKORATÍVNYCH MATERIÁLOV (jeden rad, neklikateľné) ═══ */}
        <section className="mb-10">
          <div className="flex flex-nowrap gap-3 overflow-x-auto opacity-50">
            {DASHBOARD_MATERIALS.map((material) => (
              <div
                key={material.key}
                className="relative flex-shrink-0 overflow-hidden rounded-xl border"
                style={{
                  borderColor: 'rgba(192,192,192,0.15)',
                  width: '80px',
                  height: '80px',
                }}
              >
                <img
                  src={material.img}
                  alt={material.label}
                  className="h-full w-full object-cover"
                />
                <div
                  className="absolute inset-0"
                  style={{
                    background:
                      'linear-gradient(to top, rgba(9,8,7,0.85) 0%, transparent 70%)',
                  }}
                />
                <p
                  className="absolute bottom-1 left-1 right-1 text-center text-[9px] uppercase tracking-wider"
                  style={{ color: '#c0c0c0' }}
                >
                  {material.label}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
