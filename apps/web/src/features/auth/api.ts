import { http } from '../../lib/api/http';
import { AuthResponse, LoginResponse, MeResponse } from './types';
import { LoginInput } from './schemas';

let browserCsrfToken: string | null = null;

async function issueBrowserCsrf(): Promise<string> {
  const result = await http.get<{ csrfToken: string }>('/auth/browser/csrf');
  browserCsrfToken = result.csrfToken;
  return result.csrfToken;
}

function rememberBrowserCsrf(response: LoginResponse): LoginResponse {
  browserCsrfToken = response.csrfToken ?? null;
  return response;
}

export const authApi = {
  login: async (data: LoginInput) =>
    rememberBrowserCsrf(await http.post<LoginResponse>('/auth/browser/login', data)),

  twoFactorLogin: async (twoFactorToken: string, code: string) =>
    rememberBrowserCsrf(await http.post<LoginResponse>('/auth/browser/2fa/login', { twoFactorToken, code })),

  googleLogin: (credential: string) =>
    http.post<AuthResponse>('/auth/google', { credential }),

  logout: async (_refreshToken?: string | null) => {
    const csrf = browserCsrfToken ?? await issueBrowserCsrf();
    return http.post('/auth/browser/logout', {}, { headers: { 'X-CSRF-Token': csrf } });
  },

  refreshBrowser: async () => {
    const csrf = browserCsrfToken ?? await issueBrowserCsrf();
    const result = await http.post<LoginResponse>(
      '/auth/browser/refresh',
      undefined,
      { headers: { 'X-CSRF-Token': csrf } },
    );
    browserCsrfToken = result.csrfToken ?? null;
    return result;
  },

  getMe: () => http.get<MeResponse>('/auth/me'),

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
