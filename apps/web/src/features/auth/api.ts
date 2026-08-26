import { http } from '../../lib/api/http';
import { AuthResponse, MeResponse } from './types';
import { LoginInput } from './schemas';

export const authApi = {
  login: (data: LoginInput) =>
    http.post<AuthResponse>('/auth/login', data),

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
