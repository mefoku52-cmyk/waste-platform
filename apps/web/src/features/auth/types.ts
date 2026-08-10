import { BaseEntity } from '../../lib/types/common';

export interface User extends BaseEntity {
  email: string;
  first_name: string;
  last_name: string;
  role?: string;
  status?: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}
