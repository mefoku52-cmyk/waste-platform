import { config } from '../config';
import { tokenStore } from '../auth/token-store';
import { ApiError, toApiError } from './api-error';

type HttpOptions = RequestInit & { timeoutMs?: number };

async function request<T>(path: string, options: HttpOptions = {}): Promise<T> {
  const baseUrl = config.apiBaseUrl;
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  const token = tokenStore.getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? 20000;
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    const { timeoutMs: _ignoredTimeout, ...fetchOptions } = options;
    response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
  } catch (err) {
    window.clearTimeout(timer);
    const aborted = err instanceof DOMException && err.name === 'AbortError';
    throw new ApiError(
      aborted ? `Server neodpovedal do ${Math.round(timeoutMs / 1000)} s` : 'Failed to fetch',
      0,
    );
  }
  window.clearTimeout(timer);

  if (!response.ok) {
    if (response.status === 401) {
      tokenStore.clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }

    const errorData = await response.json().catch(() => ({}));
    throw toApiError(response.status, errorData);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const http = {
  get: <T>(path: string, options?: HttpOptions) =>
    request<T>(path, { ...options, method: 'GET' }),

  post: <T>(path: string, body?: unknown, options?: HttpOptions) =>
    request<T>(path, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown, options?: HttpOptions) =>
    request<T>(path, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, options?: HttpOptions) =>
    request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, options?: HttpOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};
