import { User } from '../auth/types';

export interface AdminStats {
  total_users: number;
  total_listings: number;
  total_companies: number;
  pending_verifications: number;
}

export interface UserManagement extends User {
  is_active: boolean;
  last_login?: string;
}
