import { config } from '../config';
import { tokenStore } from '../auth/token-store';

export type ApiError = {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${config.apiBaseUrl}${path}`;
  const token = tokenStore.getToken();

  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      tokenStore.clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    
    const errorData = await response.json().catch(() => ({}));
    throw {
      message: errorData.message || 'An unexpected error occurred',
      status: response.status,
      errors: errorData.errors,
    } as ApiError;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const http = {
  get: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body: any, options?: RequestInit) => 
    request<T>(path, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: any, options?: RequestInit) => 
    request<T>(path, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: any, options?: RequestInit) => 
    request<T>(path, { ...options, method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string, options?: RequestInit) => request<T>(path, { ...options, method: 'DELETE' }),
};
