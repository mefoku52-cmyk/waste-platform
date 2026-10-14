import { cache } from 'react';

import { PublicCompanyPage } from './types';

/**
 * Absolútna základná URL backendu pre server-side fetch (SSR).
 *
 * Server komponent nemôže použiť relatívnu URL (`/api/v1`). Preto:
 * 1) ak je `NEXT_PUBLIC_API_BASE_URL` absolútna (obsahuje `http`) → použi ju,
 * 2) inak použi `API_PROXY_TARGET` (interná adresa backendu, napr. Render),
 * 3) fallback na lokálny dev backend.
 */
function serverApiBase(): string {
  const configured = (process.env.NEXT_PUBLIC_API_BASE_URL || '').trim();
  if (configured.startsWith('http')) return configured.replace(/\/$/, '');
  const target = (process.env.API_PROXY_TARGET || 'http://localhost:8001').trim();
  return `${target.replace(/\/$/, '')}/api/v1`;
}

async function serverGet<T>(path: string): Promise<T | null> {
  const url = `${serverApiBase()}${path.startsWith('/') ? path : `/${path}`}`;
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/**
 * Načíta verejnú firemnú stránku. `cache()` deduplikuje volanie medzi
 * `generateMetadata` a samotným server komponentom v rámci jedného requestu.
 */
export const fetchPublicCompanyPage = cache(
  async (slug: string): Promise<PublicCompanyPage | null> => {
    if (!slug) return null;
    return serverGet<PublicCompanyPage>(
      `/public/company-pages/${encodeURIComponent(slug)}`,
    );
  },
);

/** Zoznam zverejnených slugov pre sitemap. */
export async function fetchPublishedSlugs(): Promise<
  { slug: string; updatedAt: string | null }[]
> {
  const data = await serverGet<{
    items: { slug: string; updatedAt: string | null }[];
  }>('/public/company-pages');
  return data?.items ?? [];
}
