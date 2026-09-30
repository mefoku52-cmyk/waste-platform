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
