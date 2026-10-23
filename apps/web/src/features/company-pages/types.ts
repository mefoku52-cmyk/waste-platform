// Verejná firemná stránka — typy zrkadlia backend schémy
// (app/modules/company_pages/presentation/schemas.py).

export type PageStatus = 'draft' | 'published';

export type CompanyPageData = {
  id: string | null;
  companyId: string;
  slug: string;
  status: PageStatus | string;
  exists: boolean;
  displayName: string | null;
  tagline: string | null;
  aboutShort: string | null;
  aboutLong: string | null;
  services: string | null;
  specialization: string | null;
  certifications: string | null;
  openingHours: string | null;
  languages: string | null;
  categories: string | null;
  area: string | null;
  publicEmail: string | null;
  publicPhone: string | null;
  publicWebsite: string | null;
  seoTitle: string | null;
  seoDescription: string | null;
  publishedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  missingForPublish: string[];
};

export type CompanyPageUpsertInput = {
  slug?: string;
  displayName?: string | null;
  tagline?: string | null;
  aboutShort?: string | null;
  aboutLong?: string | null;
  services?: string | null;
  specialization?: string | null;
  certifications?: string | null;
  openingHours?: string | null;
  languages?: string | null;
  categories?: string | null;
  area?: string | null;
  publicEmail?: string | null;
  publicPhone?: string | null;
  publicWebsite?: string | null;
  seoTitle?: string | null;
  seoDescription?: string | null;
};

export type CompanyPhotoData = {
  id: string;
  fileUrl: string;
  caption: string | null;
  altText: string | null;
  position: number;
  isPrimary: boolean;
  createdAt: string | null;
};

export type PhotosResponse = {
  items: CompanyPhotoData[];
  meta: Record<string, unknown>;
};

export type CompanyPhotoQuota = {
  uploadedThisYear: number;
  quotaPerYear: number;
  remainingThisYear: number;
  calendarYear: number;
  total: number;
};

export type SlugAvailability = {
  slug: string;
  available: boolean;
  reason: string;
};

export type PageResponse = { data: CompanyPageData };

// ── Recenzie (privátne, pre editor/moderáciu) ──────────────────
export type ReviewStatus = 'pending' | 'approved' | 'rejected';

export type ReviewData = {
  id: string;
  companyId: string;
  authorUserId: string | null;
  rating: number;
  title: string | null;
  body: string | null;
  status: ReviewStatus | string;
  moderatedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ReviewsResponse = {
  items: ReviewData[];
  meta: { page: number; pageSize: number; total: number } & Record<string, unknown>;
};

// ── Verejná projekcia (pre SSR stránku) ───────────────────────
export type PublicCompanyInfo = {
  displayName: string;
  legalName: string | null;
  companyType: string | null;
  city: string | null;
  countryCode: string | null;
  verified: boolean;
  sellerCapability: boolean;
  buyerCapability: boolean;
  logisticsCapability: boolean;
  logoUrl: string | null;
};

export type PublicCompanyPhoto = {
  url: string;
  caption: string | null;
  altText: string | null;
  position: number;
  isPrimary: boolean;
};

export type PublicCompanyListing = {
  id: string;
  title: string;
  materialType: string | null;
  quantity: number | null;
  unit: string | null;
  price: number | null;
  currency: string | null;
  location: string | null;
  condition: string | null;
  imageUrl: string | null;
};

export type PublicCompanyReview = {
  id: string;
  rating: number;
  title: string | null;
  body: string | null;
  createdAt: string | null;
};

export type PublicCompanyPage = {
  slug: string;
  publishedAt: string | null;
  displayName: string;
  tagline: string | null;
  aboutShort: string | null;
  aboutLong: string | null;
  services: string | null;
  specialization: string | null;
  certifications: string | null;
  openingHours: string | null;
  languages: string | null;
  categories: string | null;
  area: string | null;
  publicEmail: string | null;
  publicPhone: string | null;
  publicWebsite: string | null;
  seoTitle: string | null;
  seoDescription: string | null;
  company: PublicCompanyInfo;
  photos: PublicCompanyPhoto[];
  listings: PublicCompanyListing[];
  ratingAverage: number | null;
  ratingCount: number;
  reviews: PublicCompanyReview[];
};
