import type { MetadataRoute } from 'next';

import { siteBaseUrlFromEnv } from '@/lib/site';
import { fetchPublishedSlugs } from '@/features/company-pages/server';

export const dynamic = 'force-dynamic';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = siteBaseUrlFromEnv();
  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = ['', '/o-nas', '/privacy', '/terms'].map((p) => ({
    url: `${base}${p || '/'}`,
    lastModified: now,
    changeFrequency: p === '' ? 'weekly' : 'monthly',
    priority: p === '' ? 1 : 0.5,
  }));

  let companyRoutes: MetadataRoute.Sitemap = [];
  try {
    const pages = await fetchPublishedSlugs();
    companyRoutes = pages.map((p) => ({
      url: `${base}/firma/${p.slug}`,
      lastModified: p.updatedAt ? new Date(p.updatedAt) : now,
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    }));
  } catch {
    companyRoutes = [];
  }

  return [...staticRoutes, ...companyRoutes];
}
