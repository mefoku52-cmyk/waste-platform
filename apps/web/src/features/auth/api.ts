import { http } from '../../lib/api/http';
import { AuthResponse, User } from './types';
import { LoginInput } from './schemas';

export const authApi = {
  login: (data: LoginInput) =>
    http.post<AuthResponse>('/api/v1/auth/login', data),

  logout: () =>
    http.post('/api/v1/auth/logout', {}),

  getMe: () =>
    http.get<User>('/api/v1/auth/me'),
};
