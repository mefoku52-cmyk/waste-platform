'use client';

// Single source of truth for the dashboard routes the AI may navigate to.
// Verified against apps/web/src/app/dashboard/** — if a page moves, fix it here
// and every client action follows. Detail routes take an entity id that is
// validated before it is interpolated, so a hostile/hallucinated id can never
// build a path outside the dashboard.

const SAFE_ID = /^[A-Za-z0-9_-]{1,64}$/;

export function safeEntityId(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const id = value.trim();
  return SAFE_ID.test(id) ? id : null;
}

export const dashboardRoutes = {
  root: '/dashboard',
  listings: '/dashboard/listings',
  listingNew: '/dashboard/listings/new',
  listing: (id: string) => `/dashboard/listings/${id}`,
  companies: '/dashboard/companies',
  companyNew: '/dashboard/companies/new',
  company: (id: string) => `/dashboard/companies/${id}`,
  inquiries: '/dashboard/inquiries',
} as const;
