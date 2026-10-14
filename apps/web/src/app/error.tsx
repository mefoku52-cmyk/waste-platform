'use client';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center"
      style={{ background: BG, color: FG }}
    >
      <h1
        className="text-2xl md:text-3xl"
        style={{ fontFamily: 'DM Serif Display, serif' }}
      >
        Niečo sa pokazilo
      </h1>
      <p className="max-w-md text-sm" style={{ color: MUTED }}>
        Nastala neočakávaná chyba. Skús to znova — ak problém pretrváva, kontaktuj
        nás.
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-full px-5 py-2 text-sm font-semibold"
        style={{ background: GOLD, color: BG }}
      >
        Skúsiť znova
      </button>
    </div>
  );
}