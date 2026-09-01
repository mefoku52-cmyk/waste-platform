#!/bin/bash
echo "KROK 5: OPRAVA FRONTEND TOKEN STORE"
cd ~/waste-platform/apps/web || exit 1

cp src/lib/auth/token-store.ts src/lib/auth/token-store.ts.bak
cp src/lib/api/http.ts src/lib/api/http.ts.bak

cat > src/lib/auth/token-store.ts << 'INNER_EOF'
export const tokenStore = {
  getToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('accessToken');
  },
  setToken: (token: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('accessToken', token);
  },
  clearToken: (): void => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
  getRefreshToken: (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refreshToken');
  },
  setRefreshToken: (token: string): void => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('refreshToken', token);
  },
};
INNER_EOF

cat > src/lib/api/http.ts << 'INNER_EOF'
import { tokenStore } from '../auth/token-store';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
  const url = `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
  const token = tokenStore.getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    if (response.status === 401) {
      tokenStore.clearToken();
      if (typeof window !== 'undefined') window.location.href = '/login';
    }
    const errorData = await response.json().catch(() => ({}));
    throw {
      message: errorData.detail || errorData.message || 'An unexpected error occurred',
      status: response.status,
      errors: errorData.errors,
    };
  }
  if (response.status === 204) return {} as T;
  return response.json();
}

export const http = {
  get: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: any, options?: RequestInit) => request<T>(path, { ...options, method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: any, options?: RequestInit) => request<T>(path, { ...options, method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: any, options?: RequestInit) => request<T>(path, { ...options, method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: 'DELETE' }),
};
INNER_EOF

echo "HOTOVO. Reštartuj frontend: cd apps/web && npm run dev"
