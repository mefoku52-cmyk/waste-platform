'use client';

const GOLD = '#c9a84c';
const BG = '#090807';

export function PromoteBadge({
  promotedUntil,
  promotedTier,
}: {
  promotedUntil?: string | null;
  promotedTier?: string | null;
}) {
  if (!promotedUntil) return null;
  const until = new Date(promotedUntil);
  if (Number.isNaN(until.getTime()) || until <= new Date()) return null;

  const isGold = promotedTier === 'gold';

  return (
    <span
      className="absolute right-3 top-3 z-10 rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.15em]"
      style={{
        background: isGold ? 'linear-gradient(135deg, #e8d48b, #c9a84c)' : GOLD,
        color: BG,
        boxShadow: isGold ? '0 0 12px rgba(232,212,139,0.6)' : 'none',
      }}
    >
      ⭐ {isGold ? 'GOLD' : 'TOP'}
    </span>
  );
}
