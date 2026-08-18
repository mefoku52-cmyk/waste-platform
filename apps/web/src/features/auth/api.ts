import { http } from '../../lib/api/http';
import { AuthResponse, MeResponse } from './types';
import { LoginInput } from './schemas';

export const authApi = {
  login: (data: LoginInput) =>
    http.post<AuthResponse>('/api/v1/auth/login', data),

  googleLogin: (credential: string) =>
    http.post<AuthResponse>('/api/v1/auth/google', { credential }),

  logout: (refreshToken: string) =>
    http.post('/api/v1/auth/logout', { refreshToken }),

  getMe: () =>
    http.get<MeResponse>('/api/v1/auth/me'),

  forgotPassword: (email: string) =>
    http.post<{ ok: boolean; message: string; resetToken?: string }>(
      '/api/v1/auth/forgot-password',
      { email }
    ),

  resetPassword: (token: string, newPassword: string) =>
    http.post<{ ok: boolean; message: string }>(
      '/api/v1/auth/reset-password',
      { token, newPassword }
    ),
};
