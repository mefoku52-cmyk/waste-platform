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
