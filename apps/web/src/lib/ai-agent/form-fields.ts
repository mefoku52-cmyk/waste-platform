'use client';

// Single source of truth for the fields the AI may fill in each dashboard form.
// Both the form components (useAiFormFilling) and the page-context builder
// import from here, so they can never drift apart.

export const LISTING_FORM_FIELDS = [
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
  'imageUrl',
] as const;

export const COMPANY_FORM_FIELDS = [
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
] as const;
