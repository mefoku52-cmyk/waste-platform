import { User } from '../auth/types';

export interface AdminStats {
  total_users: number;
  total_listings: number;
  total_companies: number;
  pending_verifications: number;
}

export interface UserManagement extends User {
  is_active?: boolean;
  isActive?: boolean;
  last_login?: string;
  lastLogin?: string;
  role_codes?: string[];
  roleCodes?: string[];
}

export interface AdminUsersResponse {
  data?: UserManagement[];
  items?: UserManagement[];
  users?: UserManagement[];
  meta?: Record<string, unknown>;
}

export interface AdminUserSummaryResponse {
  user: {
    id: string;
    email: string;
    firstName: string | null;
    lastName: string | null;
    status: string;
    lastLoginAt: string | null;
    createdAt: string | null;
    updatedAt: string | null;
  };
  counts: {
    listings?: number | null;
    inquiries?: number | null;
    memberships?: number | null;
    activity_events?: number | null;
  };
}

export interface AdminUserActivityItem {
  id: string;
  eventType: string;
  companyId: string | null;
  listingId: string | null;
  payload: string | null;
  createdAt: string | null;
}

export interface AdminUserActivityResponse {
  items: AdminUserActivityItem[];
  total: number;
}

export interface AdminCompanyListItem {
  id: string;
  status: string;
  legalName: string;
  tradingName: string | null;
  registrationNumber: string;
  email: string | null;
  phone: string | null;
  city: string | null;
  countryCode: string | null;
  subscriptionTier: string | null;
  companyType: string | null;
  photoCount: number;
  createdAt: string | null;
}

export interface AdminCompaniesResponse {
  items: AdminCompanyListItem[];
  meta: { page: number; pageSize: number; total: number };
}

export interface AdminCompanyDetail extends AdminCompanyListItem {
  taxIdentifier: string | null;
  vatIdentifier: string | null;
  websiteUrl: string | null;
  addressLine1: string | null;
  addressLine2: string | null;
  postalCode: string | null;
  sellerCapability: boolean;
  buyerCapability: boolean;
  logisticsCapability: boolean;
  verificationSubmittedAt: string | null;
  verifiedAt: string | null;
  rejectedAt: string | null;
  pageSlug: string | null;
  pageStatus: string | null;
  publicEmail: string | null;
  publicPhone: string | null;
  counts: Record<string, number>;
  memberships: {
    userId: string;
    email: string | null;
    firstName: string | null;
    lastName: string | null;
    role: string;
    status: string;
    isPrimaryContact: boolean;
  }[];
  photos: {
    id: string;
    fileUrl: string;
    caption: string | null;
    altText: string | null;
    position: number;
    isPrimary: boolean;
    createdAt: string | null;
  }[];
}

export interface AdminCompanyDetailResponse {
  data: AdminCompanyDetail;
}
