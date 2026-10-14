'use client';

const GOLD = '#c9a84c';
const BG = '#090807';
const FG = '#f3ead8';
const MUTED = '#9a8f7c';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="sk">
      <body style={{ background: BG, color: FG }}>
        <div
          className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center"
          style={{ background: BG, color: FG }}
        >
          <h1
            className="text-2xl md:text-3xl"
            style={{ fontFamily: 'DM Serif Display, serif' }}
          >
            Kritická chyba
          </h1>
          <p className="max-w-md text-sm" style={{ color: MUTED }}>
            Aplikácia narazila na kritickú chybu. Skús znova; ak problém
            pretrváva, obnov stránku.
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
      </body>
    </html>
  );
}