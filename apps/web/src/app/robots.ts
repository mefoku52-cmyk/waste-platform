import type { MetadataRoute } from 'next';

import { siteBaseUrlFromEnv } from '@/lib/site';

export default function robots(): MetadataRoute.Robots {
  const base = siteBaseUrlFromEnv();
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // Súkromné/prihlasovacie časti nezverejňujeme vyhľadávačom.
        disallow: ['/dashboard', '/api/'],
      },
    ],
    sitemap: `${base}/sitemap.xml`,
    host: base,
  };
}
