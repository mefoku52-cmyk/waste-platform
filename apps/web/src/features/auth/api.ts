import { http } from '../../lib/api/http';
import { AuthResponse, LoginResponse, MeResponse } from './types';
import { LoginInput } from './schemas';

export const authApi = {
  login: (data: LoginInput) =>
    http.post<LoginResponse>('/auth/login', data),

  twoFactorLogin: (twoFactorToken: string, code: string) =>
    http.post<LoginResponse>('/auth/2fa/login', { twoFactorToken, code }),

  googleLogin: (credential: string) =>
    http.post<AuthResponse>('/auth/google', { credential }),

  logout: (refreshToken: string) =>
    http.post('/auth/logout', { refreshToken }),

  getMe: () =>
    http.get<MeResponse>('/auth/me'),

  forgotPassword: (email: string) =>
    http.post<{ ok: boolean; message: string; resetToken?: string }>(
      '/auth/forgot-password',
      { email }
    ),

  resetPassword: (token: string, newPassword: string) =>
    http.post<{ ok: boolean; message: string }>(
      '/auth/reset-password',
      { token, newPassword }
    ),
};
