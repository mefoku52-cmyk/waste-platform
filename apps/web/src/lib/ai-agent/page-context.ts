'use client';

// Zostaví kontext aktuálnej stránky pre AI.
// Posiela sa v každom chate, aby AI vedela kde sa používateľ nachádza —
// vrátane typu stránky, entity (id + názov) a polí formulára.

import { COMPANY_FORM_FIELDS, LISTING_FORM_FIELDS } from './form-fields';

export type PageContext = {
  url: string;
  path: string;
  page_type: string;
  entity_id?: string;
  entity_label?: string;
  form_fields?: string[];
};

const MAX_LABEL_LEN = 140;

function entityLabel(): string | undefined {
  if (typeof document === 'undefined') return undefined;
  // Best-effort: the page's main heading is the listing title / company name.
  const heading = document.querySelector('h1');
  const text = heading?.textContent?.replace(/\s+/g, ' ').trim();
  if (!text) return undefined;
  return text.slice(0, MAX_LABEL_LEN);
}

function matchEntity(path: string, base: string): string | undefined {
  // Matches /dashboard/<base>/<id> and /dashboard/<base>/<id>/edit.
  const m = path.match(new RegExp(`^/dashboard/${base}/([^/]+)(?:/edit)?$`));
  return m ? m[1] : undefined;
}

export function getPageContext(): PageContext {
  if (typeof window === 'undefined') {
    return { url: '', path: '', page_type: 'unknown' };
  }
  const path = window.location.pathname;
  const url = window.location.href;

  let page_type = 'other';
  let form_fields: string[] | undefined;
  let entity_id: string | undefined;

  if (path === '/dashboard' || path === '/dashboard/') {
    page_type = 'dashboard';
  } else if (path === '/dashboard/listings/new') {
    page_type = 'listing_new';
    form_fields = [...LISTING_FORM_FIELDS];
  } else if (/^\/dashboard\/listings\/[^/]+\/edit$/.test(path)) {
    page_type = 'listing_edit';
    form_fields = [...LISTING_FORM_FIELDS];
    entity_id = matchEntity(path, 'listings');
  } else if (path === '/dashboard/listings') {
    page_type = 'listings_list';
  } else if (/^\/dashboard\/listings\/[^/]+$/.test(path)) {
    page_type = 'listing_detail';
    entity_id = matchEntity(path, 'listings');
  } else if (path === '/dashboard/companies/new') {
    page_type = 'company_new';
    form_fields = [...COMPANY_FORM_FIELDS];
  } else if (/^\/dashboard\/companies\/[^/]+\/edit$/.test(path)) {
    page_type = 'company_edit';
    form_fields = [...COMPANY_FORM_FIELDS];
    entity_id = matchEntity(path, 'companies');
  } else if (path === '/dashboard/companies') {
    page_type = 'companies_list';
  } else if (/^\/dashboard\/companies\/[^/]+$/.test(path)) {
    page_type = 'company_detail';
    entity_id = matchEntity(path, 'companies');
  } else if (path === '/dashboard/inquiries') {
    page_type = 'inquiries';
  } else if (/^\/dashboard\/chat(\/[^/]+)?$/.test(path)) {
    page_type = 'chat';
  } else if (path === '/dashboard/documents/new') {
    page_type = 'document_new';
  } else if (path === '/dashboard/documents') {
    page_type = 'documents_list';
  } else if (path === '/dashboard/settings/security') {
    page_type = 'settings_security';
  } else if (path.startsWith('/dashboard/admin')) {
    page_type = 'admin';
  }

  // Label len pre detail/edit stránky, kde je entita relevantná.
  const wants_label =
    page_type === 'listing_detail' ||
    page_type === 'listing_edit' ||
    page_type === 'company_detail' ||
    page_type === 'company_edit';
  const entity_label = wants_label ? entityLabel() : undefined;

  return {
    url,
    path,
    page_type,
    entity_id,
    entity_label,
    form_fields,
  };
}
