/** Základná verejná URL webu pre canonical, OpenGraph, sitemap a robots. */

const PRODUCTION_FALLBACK = 'https://trc-cmep.sk';
const DEVELOPMENT_FALLBACK = 'http://localhost:3001';

function normalizedPublicUrl(raw: string): string | null {
  const value = raw.trim();
  if (!value) return null;

  try {
    const parsed = new URL(value);
    if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return null;
    if (parsed.username || parsed.password) return null;
    if (parsed.pathname !== '/' || parsed.search || parsed.hash) return null;

    const hostname = parsed.hostname.toLowerCase();
    if (
      hostname === 'localhost' ||
      hostname === '127.0.0.1' ||
      hostname === '[::1]' ||
      hostname.endsWith('.localhost')
    ) {
      return null;
    }

    if (process.env.NODE_ENV === 'production' && parsed.protocol !== 'https:') {
      return null;
    }

    return parsed.origin.replace(/\/$/, '');
  } catch {
    return null;
  }
}

/** Synchronická verzia používaná aj v robots.ts a sitemap.ts. */
export function siteBaseUrlFromEnv(): string {
  const configured = normalizedPublicUrl(process.env.NEXT_PUBLIC_SITE_URL || '');
  if (configured) return configured;

  return process.env.NODE_ENV === 'production'
    ? PRODUCTION_FALLBACK
    : DEVELOPMENT_FALLBACK;
}

/** V produkcii sa nedôveryhodné Host hlavičky nepoužívajú ako fallback. */
export async function siteBaseUrl(): Promise<string> {
  const configured = normalizedPublicUrl(process.env.NEXT_PUBLIC_SITE_URL || '');
  if (configured) return configured;

  if (process.env.NODE_ENV === 'production') return PRODUCTION_FALLBACK;

  try {
    const { headers } = await import('next/headers');
    const h = await headers();
    const host = h.get('x-forwarded-host') || h.get('host');
    const proto = h.get('x-forwarded-proto') || 'http';

    if (
      host &&
      !host.includes(',') &&
      !/[\s/@\\]/.test(host) &&
      (proto === 'http' || proto === 'https') &&
      !/^(localhost|127\.0\.0\.1|\[::1\])(?::\d+)?$/i.test(host)
    ) {
      return `${proto}://${host}`;
    }
  } catch {
    // Build alebo kontext bez request hlavičiek.
  }

  return DEVELOPMENT_FALLBACK;
}
