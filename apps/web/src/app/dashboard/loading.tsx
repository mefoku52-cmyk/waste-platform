const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function Loading() {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center gap-3"
      style={{ background: BG, color: FG }}
    >
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-t-transparent"
        style={{ borderColor: GOLD, borderTopColor: 'transparent' }}
      />
      <p className="text-sm" style={{ color: MUTED }}>
        Načítavam…
      </p>
    </div>
  );
}
