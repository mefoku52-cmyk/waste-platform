'use client';

// Zostaví kontext aktuálnej stránky pre AI.
// Posiela sa v každom chate, aby AI vedela kde sa používateľ nachádza.

export type PageContext = {
  url: string;
  path: string;
  page_type: string;
  form_fields?: string[];
};

const FORM_REGISTRY: Record<string, string[]> = {
  '/dashboard/listings/new': [
    'title',
    'materialType',
    'quantity',
    'unit',
    'price',
    'currency',
    'condition',
    'location',
    'description',
    'companyId',
  ],
  '/dashboard/companies/new': [
    'entityType',
    'legalName',
    'tradingName',
    'registrationNumber',
    'vatIdentifier',
    'companyType',
    'countryCode',
    'addressLine1',
    'city',
    'postalCode',
    'email',
    'phone',
  ],
};

export function getPageContext(): PageContext {
  if (typeof window === 'undefined') {
    return { url: '', path: '', page_type: 'unknown' };
  }
  const path = window.location.pathname;
  const url = window.location.href;

  // Rozpoznaj typ stránky
  let page_type = 'other';
  if (path === '/dashboard') page_type = 'dashboard';
  else if (path.startsWith('/dashboard/listings/new')) page_type = 'listing_new';
  else if (path.match(/^\/dashboard\/listings\/[^/]+\/edit/)) page_type = 'listing_edit';
  else if (path.match(/^\/dashboard\/listings\/[^/]+$/)) page_type = 'listing_detail';
  else if (path === '/dashboard/listings') page_type = 'listings_list';
  else if (path === '/dashboard/companies/new') page_type = 'company_new';
  else if (path.match(/^\/dashboard\/companies\/[^/]+$/)) page_type = 'company_detail';
  else if (path === '/dashboard/companies') page_type = 'companies_list';
  else if (path.startsWith('/dashboard/inquiries')) page_type = 'inquiries';
  else if (path.startsWith('/dashboard/chat')) page_type = 'chat';

  // Polia formulára podľa URL
  const form_fields = FORM_REGISTRY[path];

  return {
    url,
    path,
    page_type,
    form_fields: form_fields ? [...form_fields] : undefined,
  };
}
