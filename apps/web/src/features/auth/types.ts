import { BaseEntity } from '../../lib/types/common';

export interface User extends BaseEntity {
  email: string;
  first_name?: string;
  last_name?: string;
  firstName?: string;
  lastName?: string;
  role?: string;
  status?: string;
  memberships?: Membership[];
  roleCodes?: string[];
  // Server-authoritativny signal platform-admin opravnenia (z /auth/me).
  // Frontend ho nesmie odvodzovat z roleCodes — tenant rola `admin` nie je
  // platform admin.
  isPlatformAdmin?: boolean;
}

export interface Membership {
  id: string;
  companyId: string;
  membershipRole?: string;
  status?: string;
  isPrimaryContact?: boolean;
}

export interface MeResponse {
  user: User;
  memberships: Membership[];
  roleCodes?: string[];
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface LoginResponse {
  requires2fa: boolean;
  twoFactorToken?: string | null;
  accessToken?: string | null;
  refreshToken?: string | null;
  tokenType?: string;
  expiresIn?: number;
}
