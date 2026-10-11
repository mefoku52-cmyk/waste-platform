'use client';

import Link from 'next/link';

// Shape of a card the backend attaches to a chat reply. Rendered as a small
// result tile next to the assistant text. The `href` is validated here too:
// only internal /dashboard/* routes are ever turned into a link.
export type AiCard = {
  type: string;
  id?: string | null;
  title: string;
  subtitle?: string;
  image?: string | null;
  status?: string | null;
  href?: string | null;
  meta?: { label: string; value: string }[];
};

function safeHref(href: unknown): string | null {
  if (typeof href !== 'string') return null;
  if (!href.startsWith('/dashboard/') || href.startsWith('//')) return null;
  return href;
}

function Card({ card }: { card: AiCard }) {
  const href = safeHref(card.href);
  const body = (
    <div
      className="flex h-full flex-col gap-1 rounded-xl border p-3 text-sm transition"
      style={{
        borderColor: 'rgba(201,168,76,0.25)',
        background: '#17140d',
        color: '#f3e6c4',
      }}
    >
      <div className="flex items-start gap-2">
        {card.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={card.image}
            alt=""
            className="h-10 w-10 flex-shrink-0 rounded-lg object-cover"
          />
        ) : null}
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold" style={{ color: '#f3e6c4' }}>
            {card.title}
          </p>
          {card.subtitle ? (
            <p className="truncate text-xs" style={{ color: '#9a8f7c' }}>
              {card.subtitle}
            </p>
          ) : null}
        </div>
        {card.status ? (
          <span
            className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide"
            style={{ background: 'rgba(201,168,76,0.15)', color: '#c9a84c' }}
          >
            {card.status}
          </span>
        ) : null}
      </div>

      {Array.isArray(card.meta) && card.meta.length > 0 ? (
        <dl className="mt-1 grid grid-cols-2 gap-x-3 gap-y-1">
          {card.meta.map((m, i) => (
            <div key={i} className="flex items-baseline justify-between gap-2">
              <dt className="truncate text-xs" style={{ color: '#9a8f7c' }}>
                {m.label}
              </dt>
              <dd className="text-xs font-medium" style={{ color: '#f3e6c4' }}>
                {m.value}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      {href ? (
        <span className="mt-1 text-xs font-semibold" style={{ color: '#c9a84c' }}>
          Otvoriť →
        </span>
      ) : null}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        {body}
      </Link>
    );
  }
  return body;
}

export function AiCardList({ cards }: { cards: AiCard[] }) {
  if (!cards || cards.length === 0) return null;
  return (
    <div className="flex flex-col gap-2">
      {cards.map((card, i) => (
        <Card key={`${card.type}-${card.id ?? i}`} card={card} />
      ))}
    </div>
  );
}
