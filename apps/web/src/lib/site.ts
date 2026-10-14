/** Základná verejná URL webu (pre canonical, OpenGraph, sitemap). */

const FALLBACK = 'http://localhost:3001';

/** Synchronná verzia z env (použiteľná aj v sitemap.ts/robots.ts). */
export function siteBaseUrlFromEnv(): string {
  const env = (process.env.NEXT_PUBLIC_SITE_URL || '').trim();
  return (env || FALLBACK).replace(/\/$/, '');
}

/** Počas requestu: env → hlavičky (proxy) → fallback. */
export async function siteBaseUrl(): Promise<string> {
  const env = (process.env.NEXT_PUBLIC_SITE_URL || '').trim();
  if (env) return env.replace(/\/$/, '');
  try {
    const { headers } = await import('next/headers');
    const h = await headers();
    const host = h.get('x-forwarded-host') || h.get('host');
    const proto = h.get('x-forwarded-proto') || 'https';
    if (host) return `${proto}://${host}`;
  } catch {
    // mimo request kontextu (build) → fallback
  }
  return FALLBACK;
}
