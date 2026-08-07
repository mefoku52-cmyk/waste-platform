# ============================================
# FILE: apps/web/package.json
# ============================================
{
  "name": "@cmep/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3001",
    "build": "next build",
    "start": "next start --port 3001",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.9.0",
    "@tanstack/react-query": "^5.59.0",
    "@tanstack/react-query-devtools": "^5.59.0",
    "clsx": "^2.1.1",
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-hook-form": "^7.53.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.8.1",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3"
  }
}

# ============================================
# FILE: apps/web/tsconfig.json
# ============================================
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      { "name": "next" }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["next-env.d.ts", "src/**/*.ts", "src/**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

# ============================================
# FILE: apps/web/next.config.js
# ============================================
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: false
  }
};

module.exports = nextConfig;

# ============================================
# FILE: apps/web/postcss.config.js
# ============================================
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
};

# ============================================
# FILE: apps/web/tailwind.config.js
# ============================================
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/features/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#01696f",
          hover: "#0c4e54",
          active: "#0f3638"
        }
      }
    }
  },
  plugins: []
};

# ============================================
# FILE: apps/web/next-env.d.ts
# ============================================
/// <reference types="next" />
/// <reference types="next/image-types/global" />

# ============================================
# FILE: apps/web/src/app/globals.css
# ============================================
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-bg: #f7f6f2;
  --color-surface: #f9f8f5;
  --color-surface-2: #fbfbf9;
  --color-border: #d4d1ca;
  --color-text: #28251d;
  --color-text-muted: #7a7974;
  --color-primary: #01696f;
  --color-primary-hover: #0c4e54;
  --color-danger: #a12c7b;
  --color-success: #437a22;
}

html, body {
  margin: 0;
  padding: 0;
  min-height: 100%;
  background: var(--color-bg);
  color: var(--color-text);
}

body {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

a {
  color: inherit;
  text-decoration: none;
}

input, select, textarea, button {
  font: inherit;
}

.container-page {
  @apply mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8;
}

.card {
  @apply rounded-xl border border-stone-300 bg-white shadow-sm;
}

.input {
  @apply w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200;
}

.label {
  @apply mb-1 block text-sm font-medium text-stone-800;
}

.button-primary {
  @apply inline-flex items-center justify-center rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60;
}

.button-secondary {
  @apply inline-flex items-center justify-center rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-900 transition hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-60;
}

.button-danger {
  @apply inline-flex items-center justify-center rounded-lg bg-fuchsia-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-fuchsia-900 disabled:cursor-not-allowed disabled:opacity-60;
}

.badge {
  @apply inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium;
}

.badge-neutral {
  @apply bg-stone-100 text-stone-700;
}

.badge-success {
  @apply bg-green-100 text-green-700;
}

.badge-warning {
  @apply bg-amber-100 text-amber-700;
}

.badge-danger {
  @apply bg-fuchsia-100 text-fuchsia-700;
}

.table-wrap {
  @apply overflow-x-auto;
}

.table {
  @apply min-w-full border-collapse;
}

.table th {
  @apply border-b border-stone-200 px-3 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-600;
}

.table td {
  @apply border-b border-stone-200 px-3 py-3 text-sm text-stone-900 align-top;
}

.page-title {
  @apply text-2xl font-semibold tracking-tight text-stone-900;
}

.page-subtitle {
  @apply mt-1 text-sm text-stone-600;
}

.field-error {
  @apply mt-1 text-xs text-fuchsia-800;
}

.section-stack {
  @apply space-y-6;
}

.stats-grid {
  @apply grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4;
}

.stat-card {
  @apply rounded-xl border border-stone-300 bg-white p-5 shadow-sm;
}

.stat-label {
  @apply text-sm text-stone-600;
}

.stat-value {
  @apply mt-2 text-2xl font-semibold text-stone-900;
}

.shell {
  @apply min-h-screen bg-stone-50;
}

.shell-grid {
  @apply grid min-h-screen grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)];
}

.sidebar {
  @apply border-b border-stone-200 bg-white lg:border-b-0 lg:border-r;
}

.sidebar-nav {
  @apply flex flex-col gap-1 p-4;
}

.sidebar-link {
  @apply rounded-lg px-3 py-2 text-sm font-medium text-stone-700 transition hover:bg-stone-100 hover:text-stone-900;
}

.sidebar-link-active {
  @apply bg-teal-50 text-teal-900;
}

.header-bar {
  @apply flex flex-col gap-3 border-b border-stone-200 bg-white px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6;
}

.content-area {
  @apply p-4 sm:p-6;
}

.filters-grid {
  @apply grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4;
}

.form-grid {
  @apply grid grid-cols-1 gap-4 md:grid-cols-2;
}

.form-grid-wide {
  @apply grid grid-cols-1 gap-4;
}

.muted {
  @apply text-sm text-stone-600;
}

.empty-state {
  @apply rounded-xl border border-dashed border-stone-300 bg-white p-8 text-center text-stone-600;
}

# ============================================
# FILE: apps/web/src/lib/config.ts
# ============================================
export const appConfig = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1",
  appName: "Circular Materials Exchange Platform"
};

# ============================================
# FILE: apps/web/src/lib/types/common.ts
# ============================================
export type UUID = string;

export type PaginationMeta = {
  page: number;
  pageSize: number;
  total: number;
};

export type ApiError = {
  code: string;
  message: string;
  correlationId?: string | null;
  details?: Record<string, unknown> | null;
  currentStatus?: string;
  attemptedStatus?: string;
  allowedTransitions?: string[];
};

# ============================================
# FILE: apps/web/src/lib/query-client.ts
# ============================================
import { QueryClient } from "@tanstack/react-query";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        gcTime: 5 * 60_000,
        retry: 1,
        refetchOnWindowFocus: false
      },
      mutations: {
        retry: 0
      }
    }
  });
}

# ============================================
# FILE: apps/web/src/lib/auth/token-store.ts
# ============================================
const ACCESS_TOKEN_KEY = "cmep_access_token";
const REFRESH_TOKEN_KEY = "cmep_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(tokens: { accessToken: string; refreshToken: string }) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

# ============================================
# FILE: apps/web/src/lib/auth/auth-events.ts
# ============================================
export const AUTH_CHANGED_EVENT = "cmep:auth-changed";

export function emitAuthChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
  }
}

# ============================================
# FILE: apps/web/src/lib/api/http.ts
# ============================================
import { appConfig } from "@/lib/config";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth/token-store";
import { emitAuthChanged } from "@/lib/auth/auth-events";
import type { ApiError } from "@/lib/types/common";

type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
  retryOn401?: boolean;
};

let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      emitAuthChanged();
      return false;
    }

    const response = await fetch(`${appConfig.apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ refreshToken })
    });

    if (!response.ok) {
      clearTokens();
      emitAuthChanged();
      return false;
    }

    const data = await response.json();
    setTokens({
      accessToken: data.accessToken,
      refreshToken: data.refreshToken
    });
    emitAuthChanged();
    return true;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    headers = {},
    auth = true,
    retryOn401 = true
  } = options;

  const accessToken = auth ? getAccessToken() : null;

  const response = await fetch(`${appConfig.apiBaseUrl}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(auth && accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store"
  });

  if (response.status === 401 && auth && retryOn401) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiRequest<T>(path, { ...options, retryOn401: false });
    }
  }

  if (!response.ok) {
    let errorPayload: ApiError = {
      code: "http_error",
      message: "Request failed"
    };
    try {
      errorPayload = await response.json();
    } catch {
      errorPayload = {
        code: "http_error",
        message: `Request failed with status ${response.status}`
      };
    }
    throw errorPayload;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

# ============================================
# FILE: apps/web/src/lib/utils/cn.ts
# ============================================
import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

# ============================================
# FILE: apps/web/src/components/providers/app-providers.tsx
# ============================================
"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ReactNode, useState } from "react";

import { createQueryClient } from "@/lib/query-client";
import { AuthBootstrap } from "@/features/auth/components/auth-bootstrap";

type Props = {
  children: ReactNode;
};

export function AppProviders({ children }: Props) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap>{children}</AuthBootstrap>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

# ============================================
# FILE: apps/web/src/components/layout/app-shell.tsx
# ============================================
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { PropsWithChildren } from "react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { useLogout } from "@/features/auth/hooks/use-logout";
import { cn } from "@/lib/utils/cn";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/companies", label: "Companies" },
  { href: "/admin/users", label: "Admin" }
];

export function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: currentUser } = useCurrentUser();
  const logoutMutation = useLogout();

  return (
    <div className="shell">
      <div className="shell-grid">
        <aside className="sidebar">
          <div className="border-b border-stone-200 p-4">
            <div className="text-lg font-semibold text-stone-900">CMEP</div>
            <div className="mt-1 text-sm text-stone-600">B2B circular materials marketplace</div>
          </div>
          <nav className="sidebar-nav">
            {navItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn("sidebar-link", isActive && "sidebar-link-active")}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="min-w-0">
          <header className="header-bar">
            <div>
              <div className="text-sm text-stone-600">Authenticated workspace</div>
              <div className="text-base font-medium text-stone-900">
                {currentUser?.user.firstName} {currentUser?.user.lastName}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="button-secondary"
                onClick={() => router.push("/companies")}
              >
                Companies
              </button>
              <button
                type="button"
                className="button-danger"
                disabled={logoutMutation.isPending}
                onClick={() => logoutMutation.mutate()}
              >
                Logout
              </button>
            </div>
          </header>
          <main className="content-area">{children}</main>
        </div>
      </div>
    </div>
  );
}

# ============================================
# FILE: apps/web/src/components/ui/button.tsx
# ============================================
"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/utils/cn";

type Variant = "primary" | "secondary" | "danger";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
};

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { className, variant = "primary", ...props },
  ref
) {
  const variantClass =
    variant === "primary"
      ? "button-primary"
      : variant === "danger"
        ? "button-danger"
        : "button-secondary";

  return <button ref={ref} className={cn(variantClass, className)} {...props} />;
});

# ============================================
# FILE: apps/web/src/components/ui/input.tsx
# ============================================
"use client";

import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, ...props }, ref) {
    return <input ref={ref} className={cn("input", className)} {...props} />;
  }
);

# ============================================
# FILE: apps/web/src/components/ui/select.tsx
# ============================================
"use client";

import { SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, ...props }, ref) {
    return <select ref={ref} className={cn("input", className)} {...props} />;
  }
);

# ============================================
# FILE: apps/web/src/components/ui/textarea.tsx
# ============================================
"use client";

import { TextareaHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils/cn";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  function Textarea({ className, ...props }, ref) {
    return <textarea ref={ref} className={cn("input min-h-[120px]", className)} {...props} />;
  }
);

# ============================================
# FILE: apps/web/src/components/ui/form-field.tsx
# ============================================
import { ReactNode } from "react";

type Props = {
  label: string;
  error?: string;
  children: ReactNode;
};

export function FormField({ label, error, children }: Props) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {error ? <p className="field-error">{error}</p> : null}
    </div>
  );
}

# ============================================
# FILE: apps/web/src/components/ui/status-badge.tsx
# ============================================
import { cn } from "@/lib/utils/cn";

type Props = {
  status: string;
};

export function StatusBadge({ status }: Props) {
  const normalized = status.toLowerCase();

  const className =
    normalized.includes("approved") ||
    normalized.includes("verified") ||
    normalized.includes("active") ||
    normalized.includes("published") ||
    normalized.includes("completed")
      ? "badge badge-success"
      : normalized.includes("rejected") ||
          normalized.includes("cancelled") ||
          normalized.includes("disputed") ||
          normalized.includes("suspended")
        ? "badge badge-danger"
        : "badge badge-warning";

  return <span className={cn(className)}>{status}</span>;
}

# ============================================
# FILE: apps/web/src/components/ui/page-header.tsx
# ============================================
import { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, actions }: Props) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
    </div>
  );
}

# ============================================
# FILE: apps/web/src/components/ui/data-table.tsx
# ============================================
import { ReactNode } from "react";

type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
};

type Props<T> = {
  columns: Column<T>[];
  rows: T[];
  emptyMessage?: string;
};

export function DataTable<T>({ columns, rows, emptyMessage = "No data found." }: Props<T>) {
  if (rows.length === 0) {
    return <div className="empty-state">{emptyMessage}</div>;
  }

  return (
    <div className="table-wrap card">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key}>{column.render(row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

# ============================================
# FILE: apps/web/src/features/auth/types.ts
# ============================================
import type { UUID } from "@/lib/types/common";

export type LoginRequest = {
  email: string;
  password: string;
};

export type RegisterRequest = {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  displayName?: string | null;
  phone?: string | null;
  locale?: string | null;
  timezone?: string | null;
};

export type AuthTokenPair = {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
};

export type UserData = {
  id: UUID;
  status: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName?: string | null;
  phone?: string | null;
  locale?: string | null;
  timezone?: string | null;
  lastLoginAt?: string | null;
  createdAt: string;
  createdByUserId?: UUID | null;
  updatedAt: string;
  updatedByUserId?: UUID | null;
};

export type MembershipContext = {
  id: UUID;
  companyId: UUID;
  membershipRole: string;
  status: string;
  isPrimaryContact: boolean;
};

export type CurrentUserResponse = {
  user: UserData;
  roleCodes: string[];
  memberships: MembershipContext[];
};

# ============================================
# FILE: apps/web/src/features/auth/schemas.ts
# ============================================
import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Zadaj platný email"),
  password: z.string().min(8, "Heslo musí mať aspoň 8 znakov")
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  email: z.string().email("Zadaj platný email"),
  password: z.string().min(8, "Heslo musí mať aspoň 8 znakov"),
  firstName: z.string().min(1, "Meno je povinné"),
  lastName: z.string().min(1, "Priezvisko je povinné"),
  displayName: z.string().optional(),
  phone: z.string().optional(),
  locale: z.string().optional(),
  timezone: z.string().optional()
});

export type RegisterFormValues = z.infer<typeof registerSchema>;

# ============================================
# FILE: apps/web/src/features/auth/api.ts
# ============================================
import { apiRequest } from "@/lib/api/http";
import type { AuthTokenPair, CurrentUserResponse, LoginRequest, RegisterRequest } from "@/features/auth/types";
import type { UserData } from "@/features/auth/types";

export async function login(payload: LoginRequest): Promise<AuthTokenPair> {
  return apiRequest<AuthTokenPair>("/auth/login", {
    method: "POST",
    auth: false,
    body: payload
  });
}

export async function refreshSession(refreshToken: string): Promise<AuthTokenPair> {
  return apiRequest<AuthTokenPair>("/auth/refresh", {
    method: "POST",
    auth: false,
    body: { refreshToken }
  });
}

export async function logout(refreshToken?: string | null): Promise<void> {
  await apiRequest<void>("/auth/logout", {
    method: "POST",
    body: { refreshToken: refreshToken ?? null }
  });
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  return apiRequest<CurrentUserResponse>("/auth/me");
}

export async function register(payload: RegisterRequest): Promise<{ data: UserData }> {
  return apiRequest<{ data: UserData }>("/users", {
    method: "POST",
    body: payload
  });
}

# ============================================
# FILE: apps/web/src/features/auth/hooks/use-login.ts
# ============================================
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { login } from "@/features/auth/api";
import { emitAuthChanged } from "@/lib/auth/auth-events";
import { setTokens } from "@/lib/auth/token-store";

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: login,
    onSuccess: async (data) => {
      setTokens({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken
      });
      emitAuthChanged();
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    }
  });
}

# ============================================
# FILE: apps/web/src/features/auth/hooks/use-logout.ts
# ============================================
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { logout } from "@/features/auth/api";
import { clearTokens, getRefreshToken } from "@/lib/auth/token-store";
import { emitAuthChanged } from "@/lib/auth/auth-events";

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken();
      try {
        await logout(refreshToken);
      } finally {
        clearTokens();
        emitAuthChanged();
      }
    },
    onSuccess: async () => {
      await queryClient.clear();
      router.replace("/login");
    }
  });
}

# ============================================
# FILE: apps/web/src/features/auth/hooks/use-current-user.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";

import { getCurrentUser } from "@/features/auth/api";
import { getAccessToken } from "@/lib/auth/token-store";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: !!getAccessToken()
  });
}

# ============================================
# FILE: apps/web/src/features/auth/hooks/use-auth-required.ts
# ============================================
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useCurrentUser } from "@/features/auth/hooks/use-current-user";
import { getAccessToken } from "@/lib/auth/token-store";

export function useAuthRequired() {
  const router = useRouter();
  const query = useCurrentUser();

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
    }
  }, [router]);

  useEffect(() => {
    if (query.isError) {
      router.replace("/login");
    }
  }, [query.isError, router]);

  return query;
}

# ============================================
# FILE: apps/web/src/features/auth/hooks/use-register.ts
# ============================================
"use client";

import { useMutation } from "@tanstack/react-query";
import { register } from "@/features/auth/api";

export function useRegister() {
  return useMutation({
    mutationFn: register
  });
}

# ============================================
# FILE: apps/web/src/features/auth/components/auth-bootstrap.tsx
# ============================================
"use client";

import { ReactNode, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { AUTH_CHANGED_EVENT } from "@/lib/auth/auth-events";

type Props = {
  children: ReactNode;
};

export function AuthBootstrap({ children }: Props) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const handler = () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
    };
    window.addEventListener(AUTH_CHANGED_EVENT, handler);
    return () => window.removeEventListener(AUTH_CHANGED_EVENT, handler);
  }, [queryClient]);

  return <>{children}</>;
}

# ============================================
# FILE: apps/web/src/features/auth/components/login-form.tsx
# ============================================
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/features/auth/hooks/use-login";
import { loginSchema, type LoginFormValues } from "@/features/auth/schemas";

export function LoginForm() {
  const router = useRouter();
  const loginMutation = useLogin();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const onSubmit = form.handleSubmit(async (values) => {
    await loginMutation.mutateAsync(values);
    router.replace("/dashboard");
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <FormField label="Email" error={form.formState.errors.email?.message}>
        <Input type="email" {...form.register("email")} />
      </FormField>

      <FormField label="Password" error={form.formState.errors.password?.message}>
        <Input type="password" {...form.register("password")} />
      </FormField>

      {loginMutation.error ? (
        <p className="field-error">{(loginMutation.error as { message?: string }).message ?? "Login failed"}</p>
      ) : null}

      <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
        {loginMutation.isPending ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}

# ============================================
# FILE: apps/web/src/features/auth/components/register-form.tsx
# ============================================
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { useRegister } from "@/features/auth/hooks/use-register";
import { registerSchema, type RegisterFormValues } from "@/features/auth/schemas";

export function RegisterForm() {
  const router = useRouter();
  const registerMutation = useRegister();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      firstName: "",
      lastName: "",
      displayName: "",
      phone: "",
      locale: "sk",
      timezone: "Europe/Bratislava"
    }
  });

  const onSubmit = form.handleSubmit(async (values) => {
    await registerMutation.mutateAsync(values);
    router.replace("/login");
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="form-grid">
        <FormField label="First name" error={form.formState.errors.firstName?.message}>
          <Input {...form.register("firstName")} />
        </FormField>
        <FormField label="Last name" error={form.formState.errors.lastName?.message}>
          <Input {...form.register("lastName")} />
        </FormField>
      </div>

      <FormField label="Email" error={form.formState.errors.email?.message}>
        <Input type="email" {...form.register("email")} />
      </FormField>

      <FormField label="Password" error={form.formState.errors.password?.message}>
        <Input type="password" {...form.register("password")} />
      </FormField>

      <div className="form-grid">
        <FormField label="Display name" error={form.formState.errors.displayName?.message}>
          <Input {...form.register("displayName")} />
        </FormField>
        <FormField label="Phone" error={form.formState.errors.phone?.message}>
          <Input {...form.register("phone")} />
        </FormField>
      </div>

      <div className="form-grid">
        <FormField label="Locale" error={form.formState.errors.locale?.message}>
          <Input {...form.register("locale")} />
        </FormField>
        <FormField label="Timezone" error={form.formState.errors.timezone?.message}>
          <Input {...form.register("timezone")} />
        </FormField>
      </div>

      {registerMutation.error ? (
        <p className="field-error">{(registerMutation.error as { message?: string }).message ?? "Registration failed"}</p>
      ) : null}

      <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
        {registerMutation.isPending ? "Creating account..." : "Create account"}
      </Button>

      <p className="text-sm text-stone-600">
        Already have an account? <Link href="/login" className="font-medium text-teal-800">Sign in</Link>
      </p>
    </form>
  );
}

# ============================================
# FILE: apps/web/src/features/listings/types.ts
# ============================================
import type { PaginationMeta, UUID } from "@/lib/types/common";

export type ListingData = {
  id: UUID;
  status: string;
  materialCategory: string;
  materialSubtype: string;
  quantity: number;
  unit: string;
  purityIndicator?: string | null;
  contaminationNotes?: string | null;
  originLocation: string;
  pickupTerms?: string | null;
  deliveryTerms?: string | null;
  availabilityStart?: string | null;
  availabilityEnd?: string | null;
  priceModel: string;
  sellerCompanyId: UUID;
  createdAt: string;
  updatedAt: string;
};

export type ListingListResponse = {
  items: ListingData[];
  meta: PaginationMeta;
};

export type ListingResponse = {
  data: ListingData;
};

export type ListingFilters = {
  page?: number;
  pageSize?: number;
  status?: string;
  materialCategory?: string;
  materialSubtype?: string;
  sellerCompanyId?: UUID;
  q?: string;
};

export type ListingCreateRequest = {
  materialCategory: string;
  materialSubtype: string;
  quantity: number;
  unit: string;
  purityIndicator?: string | null;
  contaminationNotes?: string | null;
  originLocation: string;
  pickupTerms?: string | null;
  deliveryTerms?: string | null;
  availabilityStart?: string | null;
  availabilityEnd?: string | null;
  priceModel: string;
  sellerCompanyId: UUID;
};

# ============================================
# FILE: apps/web/src/features/listings/schemas.ts
# ============================================
import { z } from "zod";

export const listingFilterSchema = z.object({
  q: z.string().optional(),
  status: z.string().optional(),
  materialCategory: z.string().optional(),
  materialSubtype: z.string().optional(),
  sellerCompanyId: z.string().optional()
});

export const listingFormSchema = z.object({
  materialCategory: z.string().min(1, "Material category is required"),
  materialSubtype: z.string().min(1, "Material subtype is required"),
  quantity: z.coerce.number().positive("Quantity must be positive"),
  unit: z.string().min(1, "Unit is required"),
  purityIndicator: z.string().optional(),
  contaminationNotes: z.string().optional(),
  originLocation: z.string().min(1, "Origin location is required"),
  pickupTerms: z.string().optional(),
  deliveryTerms: z.string().optional(),
  availabilityStart: z.string().optional(),
  availabilityEnd: z.string().optional(),
  priceModel: z.string().min(1, "Price model is required"),
  sellerCompanyId: z.string().min(1, "Seller company is required")
});

export type ListingFormValues = z.infer<typeof listingFormSchema>;

# ============================================
# FILE: apps/web/src/features/listings/api.ts
# ============================================
import { apiRequest } from "@/lib/api/http";
import type { ListingCreateRequest, ListingFilters, ListingListResponse, ListingResponse } from "@/features/listings/types";

function toQueryString(filters: ListingFilters) {
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("pageSize", String(filters.pageSize));
  if (filters.status) params.set("status", filters.status);
  if (filters.materialCategory) params.set("materialCategory", filters.materialCategory);
  if (filters.materialSubtype) params.set("materialSubtype", filters.materialSubtype);
  if (filters.sellerCompanyId) params.set("sellerCompanyId", filters.sellerCompanyId);
  if (filters.q) params.set("q", filters.q);
  const value = params.toString();
  return value ? `?${value}` : "";
}

export async function getListings(filters: ListingFilters): Promise<ListingListResponse> {
  return apiRequest<ListingListResponse>(`/listings${toQueryString(filters)}`);
}

export async function getListing(listingId: string): Promise<ListingResponse> {
  return apiRequest<ListingResponse>(`/listings/${listingId}`);
}

export async function createListing(payload: ListingCreateRequest): Promise<ListingResponse> {
  return apiRequest<ListingResponse>("/listings", {
    method: "POST",
    body: payload
  });
}

export async function updateListing(listingId: string, payload: Partial<ListingCreateRequest>): Promise<ListingResponse> {
  return apiRequest<ListingResponse>(`/listings/${listingId}`, {
    method: "PATCH",
    body: payload
  });
}

# ============================================
# FILE: apps/web/src/features/listings/hooks/use-listings.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { getListings } from "@/features/listings/api";
import type { ListingFilters } from "@/features/listings/types";

export function useListings(filters: ListingFilters) {
  return useQuery({
    queryKey: ["listings", filters],
    queryFn: () => getListings(filters)
  });
}

# ============================================
# FILE: apps/web/src/features/listings/hooks/use-listing.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { getListing } from "@/features/listings/api";

export function useListing(listingId: string) {
  return useQuery({
    queryKey: ["listing", listingId],
    queryFn: () => getListing(listingId),
    enabled: !!listingId
  });
}

# ============================================
# FILE: apps/web/src/features/listings/hooks/use-create-listing.ts
# ============================================
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createListing } from "@/features/listings/api";

export function useCreateListing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createListing,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["listings"] });
    }
  });
}

# ============================================
# FILE: apps/web/src/features/listings/hooks/use-update-listing.ts
# ============================================
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { updateListing } from "@/features/listings/api";

export function useUpdateListing(listingId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => updateListing(listingId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["listings"] });
      await queryClient.invalidateQueries({ queryKey: ["listing", listingId] });
    }
  });
}

# ============================================
# FILE: apps/web/src/features/listings/components/listing-filters.tsx
# ============================================
"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { ListingFilters } from "@/features/listings/types";

type Props = {
  initialValue: ListingFilters;
  onApply: (filters: ListingFilters) => void;
};

export function ListingFilters({ initialValue, onApply }: Props) {
  const [state, setState] = useState<ListingFilters>(initialValue);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    onApply({ ...initialValue, ...state, page: 1 });
  };

  return (
    <form onSubmit={onSubmit} className="card p-4">
      <div className="filters-grid">
        <FormField label="Search">
          <Input
            value={state.q ?? ""}
            onChange={(e) => setState((prev) => ({ ...prev, q: e.target.value }))}
            placeholder="Search listings"
          />
        </FormField>

        <FormField label="Status">
          <Select
            value={state.status ?? ""}
            onChange={(e) => setState((prev) => ({ ...prev, status: e.target.value || undefined }))}
          >
            <option value="">All</option>
            <option value="draft">draft</option>
            <option value="submitted">submitted</option>
            <option value="published">published</option>
            <option value="inquiry_open">inquiry_open</option>
            <option value="negotiation">negotiation</option>
            <option value="reserved">reserved</option>
            <option value="completed">completed</option>
            <option value="archived">archived</option>
          </Select>
        </FormField>

        <FormField label="Material category">
          <Input
            value={state.materialCategory ?? ""}
            onChange={(e) => setState((prev) => ({ ...prev, materialCategory: e.target.value }))}
            placeholder="e.g. plastics"
          />
        </FormField>

        <FormField label="Material subtype">
          <Input
            value={state.materialSubtype ?? ""}
            onChange={(e) => setState((prev) => ({ ...prev, materialSubtype: e.target.value }))}
            placeholder="e.g. PET"
          />
        </FormField>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <Button type="submit">Apply filters</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            const next = { page: 1, pageSize: initialValue.pageSize ?? 20 };
            setState(next);
            onApply(next);
          }}
        >
          Reset
        </Button>
      </div>
    </form>
  );
}

# ============================================
# FILE: apps/web/src/features/listings/components/listings-table.tsx
# ============================================
import Link from "next/link";

import { DataTable } from "@/components/ui/data-table";
import { StatusBadge } from "@/components/ui/status-badge";
import type { ListingData } from "@/features/listings/types";

type Props = {
  rows: ListingData[];
};

export function ListingsTable({ rows }: Props) {
  return (
    <DataTable
      rows={rows}
      emptyMessage="No listings found for the current filters."
      columns={[
        {
          key: "material",
          header: "Material",
          render: (row) => (
            <div>
              <div className="font-medium">{row.materialCategory}</div>
              <div className="text-sm text-stone-600">{row.materialSubtype}</div>
            </div>
          )
        },
        {
          key: "quantity",
          header: "Quantity",
          render: (row) => `${row.quantity} ${row.unit}`
        },
        {
          key: "origin",
          header: "Origin",
          render: (row) => row.originLocation
        },
        {
          key: "status",
          header: "Status",
          render: (row) => <StatusBadge status={row.status} />
        },
        {
          key: "priceModel",
          header: "Price model",
          render: (row) => row.priceModel
        },
        {
          key: "actions",
          header: "Actions",
          render: (row) => (
            <Link href={`/listings/${row.id}`} className="font-medium text-teal-800">
              Detail
            </Link>
          )
        }
      ]}
    />
  );
}

# ============================================
# FILE: apps/web/src/features/listings/components/listing-form.tsx
# ============================================
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { listingFormSchema, type ListingFormValues } from "@/features/listings/schemas";
import { useCreateListing } from "@/features/listings/hooks/use-create-listing";
import { useUpdateListing } from "@/features/listings/hooks/use-update-listing";
import type { ListingData } from "@/features/listings/types";

type Props = {
  mode: "create" | "edit";
  initialData?: ListingData;
};

export function ListingForm({ mode, initialData }: Props) {
  const router = useRouter();
  const createMutation = useCreateListing();
  const updateMutation = useUpdateListing(initialData?.id ?? "");

  const mutation = mode === "create" ? createMutation : updateMutation;

  const form = useForm<ListingFormValues>({
    resolver: zodResolver(listingFormSchema),
    defaultValues: {
      materialCategory: initialData?.materialCategory ?? "",
      materialSubtype: initialData?.materialSubtype ?? "",
      quantity: initialData?.quantity ?? 0,
      unit: initialData?.unit ?? "",
      purityIndicator: initialData?.purityIndicator ?? "",
      contaminationNotes: initialData?.contaminationNotes ?? "",
      originLocation: initialData?.originLocation ?? "",
      pickupTerms: initialData?.pickupTerms ?? "",
      deliveryTerms: initialData?.deliveryTerms ?? "",
      availabilityStart: initialData?.availabilityStart ?? "",
      availabilityEnd: initialData?.availabilityEnd ?? "",
      priceModel: initialData?.priceModel ?? "",
      sellerCompanyId: initialData?.sellerCompanyId ?? ""
    }
  });

  const onSubmit = form.handleSubmit(async (values) => {
    if (mode === "create") {
      const result = await createMutation.mutateAsync(values);
      router.replace(`/listings/${result.data.id}`);
      return;
    }

    await updateMutation.mutateAsync(values);
    router.replace(`/listings/${initialData?.id}`);
  });

  return (
    <form onSubmit={onSubmit} className="card p-6">
      <div className="form-grid">
        <FormField label="Material category" error={form.formState.errors.materialCategory?.message}>
          <Input {...form.register("materialCategory")} />
        </FormField>
        <FormField label="Material subtype" error={form.formState.errors.materialSubtype?.message}>
          <Input {...form.register("materialSubtype")} />
        </FormField>
        <FormField label="Quantity" error={form.formState.errors.quantity?.message}>
          <Input type="number" step="0.01" {...form.register("quantity")} />
        </FormField>
        <FormField label="Unit" error={form.formState.errors.unit?.message}>
          <Input {...form.register("unit")} />
        </FormField>
        <FormField label="Price model" error={form.formState.errors.priceModel?.message}>
          <Input {...form.register("priceModel")} />
        </FormField>
        <FormField label="Seller company ID" error={form.formState.errors.sellerCompanyId?.message}>
          <Input {...form.register("sellerCompanyId")} />
        </FormField>
        <FormField label="Origin location" error={form.formState.errors.originLocation?.message}>
          <Input {...form.register("originLocation")} />
        </FormField>
        <FormField label="Purity indicator" error={form.formState.errors.purityIndicator?.message}>
          <Input {...form.register("purityIndicator")} />
        </FormField>
      </div>

      <div className="mt-4 form-grid">
        <FormField label="Availability start" error={form.formState.errors.availabilityStart?.message}>
          <Input type="datetime-local" {...form.register("availabilityStart")} />
        </FormField>
        <FormField label="Availability end" error={form.formState.errors.availabilityEnd?.message}>
          <Input type="datetime-local" {...form.register("availabilityEnd")} />
        </FormField>
      </div>

      <div className="mt-4 form-grid-wide">
        <FormField label="Pickup terms" error={form.formState.errors.pickupTerms?.message}>
          <Textarea {...form.register("pickupTerms")} />
        </FormField>
        <FormField label="Delivery terms" error={form.formState.errors.deliveryTerms?.message}>
          <Textarea {...form.register("deliveryTerms")} />
        </FormField>
        <FormField label="Contamination notes" error={form.formState.errors.contaminationNotes?.message}>
          <Textarea {...form.register("contaminationNotes")} />
        </FormField>
      </div>

      {mutation.error ? (
        <p className="mt-4 field-error">{(mutation.error as { message?: string }).message ?? "Saving failed"}</p>
      ) : null}

      <div className="mt-6 flex gap-3">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving..." : mode === "create" ? "Create listing" : "Save changes"}
        </Button>
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

# ============================================
# FILE: apps/web/src/features/companies/types.ts
# ============================================
import type { PaginationMeta, UUID } from "@/lib/types/common";

export type CompanyData = {
  id: UUID;
  status: string;
  legalName: string;
  tradingName?: string | null;
  registrationNumber: string;
  taxIdentifier?: string | null;
  companyType: string;
  email?: string | null;
  phone?: string | null;
  websiteUrl?: string | null;
  countryCode: string;
  addressLine1: string;
  addressLine2?: string | null;
  city: string;
  postalCode: string;
  latitude?: number | null;
  longitude?: number | null;
  sellerCapability: boolean;
  buyerCapability: boolean;
  logisticsCapability: boolean;
  verificationSubmittedAt?: string | null;
  verificationReviewedAt?: string | null;
  verificationReviewedByUserId?: UUID | null;
  verifiedAt?: string | null;
  verifiedByUserId?: UUID | null;
  rejectedAt?: string | null;
  rejectedByUserId?: UUID | null;
  createdAt: string;
  createdByUserId?: UUID | null;
  updatedAt: string;
  updatedByUserId?: UUID | null;
};

export type CompaniesResponse = {
  items: CompanyData[];
  meta: PaginationMeta;
};

export type CompanyResponse = {
  data: CompanyData;
};

export type CompanyFilters = {
  page?: number;
  pageSize?: number;
  status?: string;
  companyType?: string;
  sellerCapability?: boolean;
  buyerCapability?: boolean;
  logisticsCapability?: boolean;
  q?: string;
};

# ============================================
# FILE: apps/web/src/features/companies/api.ts
# ============================================
import { apiRequest } from "@/lib/api/http";
import type { CompaniesResponse, CompanyFilters, CompanyResponse } from "@/features/companies/types";

function toQueryString(filters: CompanyFilters) {
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("pageSize", String(filters.pageSize));
  if (filters.status) params.set("status", filters.status);
  if (filters.companyType) params.set("companyType", filters.companyType);
  if (filters.sellerCapability !== undefined) params.set("sellerCapability", String(filters.sellerCapability));
  if (filters.buyerCapability !== undefined) params.set("buyerCapability", String(filters.buyerCapability));
  if (filters.logisticsCapability !== undefined) params.set("logisticsCapability", String(filters.logisticsCapability));
  if (filters.q) params.set("q", filters.q);
  const value = params.toString();
  return value ? `?${value}` : "";
}

export async function getCompanies(filters: CompanyFilters): Promise<CompaniesResponse> {
  return apiRequest<CompaniesResponse>(`/companies${toQueryString(filters)}`);
}

export async function getCompany(companyId: string): Promise<CompanyResponse> {
  return apiRequest<CompanyResponse>(`/companies/${companyId}`);
}

# ============================================
# FILE: apps/web/src/features/companies/hooks/use-companies.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "@/features/companies/api";
import type { CompanyFilters } from "@/features/companies/types";

export function useCompanies(filters: CompanyFilters) {
  return useQuery({
    queryKey: ["companies", filters],
    queryFn: () => getCompanies(filters)
  });
}

# ============================================
# FILE: apps/web/src/features/companies/hooks/use-company.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompany } from "@/features/companies/api";

export function useCompany(companyId: string) {
  return useQuery({
    queryKey: ["company", companyId],
    queryFn: () => getCompany(companyId),
    enabled: !!companyId
  });
}

# ============================================
# FILE: apps/web/src/features/companies/components/companies-table.tsx
# ============================================
import Link from "next/link";

import { DataTable } from "@/components/ui/data-table";
import { StatusBadge } from "@/components/ui/status-badge";
import type { CompanyData } from "@/features/companies/types";

type Props = {
  rows: CompanyData[];
};

export function CompaniesTable({ rows }: Props) {
  return (
    <DataTable
      rows={rows}
      emptyMessage="No companies found."
      columns={[
        {
          key: "name",
          header: "Company",
          render: (row) => (
            <div>
              <div className="font-medium">{row.legalName}</div>
              <div className="text-sm text-stone-600">{row.registrationNumber}</div>
            </div>
          )
        },
        {
          key: "type",
          header: "Type",
          render: (row) => row.companyType
        },
        {
          key: "location",
          header: "Location",
          render: (row) => `${row.city}, ${row.countryCode}`
        },
        {
          key: "status",
          header: "Status",
          render: (row) => <StatusBadge status={row.status} />
        },
        {
          key: "actions",
          header: "Actions",
          render: (row) => (
            <Link href={`/companies/${row.id}`} className="font-medium text-teal-800">
              Detail
            </Link>
          )
        }
      ]}
    />
  );
}

# ============================================
# FILE: apps/web/src/features/admin/types.ts
# ============================================
import type { PaginationMeta, UUID } from "@/lib/types/common";

export type AdminUserData = {
  id: UUID;
  status: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName?: string | null;
  phone?: string | null;
  locale?: string | null;
  timezone?: string | null;
  lastLoginAt?: string | null;
  createdAt: string;
  updatedAt: string;
};

export type AdminUsersResponse = {
  items: AdminUserData[];
  meta: PaginationMeta;
};

export type AdminUserFilters = {
  page?: number;
  pageSize?: number;
  status?: string;
  companyId?: UUID;
  q?: string;
};

# ============================================
# FILE: apps/web/src/features/admin/api.ts
# ============================================
import { apiRequest } from "@/lib/api/http";
import type { AdminUserFilters, AdminUsersResponse } from "@/features/admin/types";

function toQueryString(filters: AdminUserFilters) {
  const params = new URLSearchParams();
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("pageSize", String(filters.pageSize));
  if (filters.status) params.set("status", filters.status);
  if (filters.companyId) params.set("companyId", filters.companyId);
  if (filters.q) params.set("q", filters.q);
  const value = params.toString();
  return value ? `?${value}` : "";
}

export async function getAdminUsers(filters: AdminUserFilters): Promise<AdminUsersResponse> {
  return apiRequest<AdminUsersResponse>(`/users${toQueryString(filters)}`);
}

# ============================================
# FILE: apps/web/src/features/admin/hooks/use-admin-users.ts
# ============================================
"use client";

import { useQuery } from "@tanstack/react-query";
import { getAdminUsers } from "@/features/admin/api";
import type { AdminUserFilters } from "@/features/admin/types";

export function useAdminUsers(filters: AdminUserFilters) {
  return useQuery({
    queryKey: ["admin", "users", filters],
    queryFn: () => getAdminUsers(filters)
  });
}

# ============================================
# FILE: apps/web/src/features/admin/components/admin-users-table.tsx
# ============================================
import { DataTable } from "@/components/ui/data-table";
import { StatusBadge } from "@/components/ui/status-badge";
import type { AdminUserData } from "@/features/admin/types";

type Props = {
  rows: AdminUserData[];
};

export function AdminUsersTable({ rows }: Props) {
  return (
    <DataTable
      rows={rows}
      emptyMessage="No users found."
      columns={[
        {
          key: "name",
          header: "User",
          render: (row) => (
            <div>
              <div className="font-medium">{row.firstName} {row.lastName}</div>
              <div className="text-sm text-stone-600">{row.email}</div>
            </div>
          )
        },
        {
          key: "status",
          header: "Status",
          render: (row) => <StatusBadge status={row.status} />
        },
        {
          key: "locale",
          header: "Locale",
          render: (row) => row.locale ?? "-"
        },
        {
          key: "timezone",
          header: "Timezone",
          render: (row) => row.timezone ?? "-"
        },
        {
          key: "lastLoginAt",
          header: "Last login",
          render: (row) => row.lastLoginAt ?? "-"
        }
      ]}
    />
  );
}

# ============================================
# FILE: apps/web/src/app/layout.tsx
# ============================================
import "./globals.css";
import { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";

export const metadata = {
  title: "CMEP Web",
  description: "Circular Materials Exchange Platform frontend"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="sk">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}

# ============================================
# FILE: apps/web/src/app/page.tsx
# ============================================
import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/dashboard");
}

# ============================================
# FILE: apps/web/src/app/(public)/login/page.tsx
# ============================================
import Link from "next/link";

import { LoginForm } from "@/features/auth/components/login-form";

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container-page flex min-h-screen items-center justify-center py-10">
        <div className="w-full max-w-md rounded-2xl border border-stone-300 bg-white p-8 shadow-sm">
          <div>
            <h1 className="text-2xl font-semibold text-stone-900">Sign in</h1>
            <p className="mt-2 text-sm text-stone-600">
              Access the B2B workspace for circular materials exchange.
            </p>
          </div>

          <div className="mt-6">
            <LoginForm />
          </div>

          <p className="mt-6 text-sm text-stone-600">
            New here? <Link href="/register" className="font-medium text-teal-800">Create an account</Link>
          </p>
        </div>
      </div>
    </main>
  );
}

# ============================================
# FILE: apps/web/src/app/(public)/register/page.tsx
# ============================================
import { RegisterForm } from "@/features/auth/components/register-form";

export default function RegisterPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <div className="container-page flex min-h-screen items-center justify-center py-10">
        <div className="w-full max-w-2xl rounded-2xl border border-stone-300 bg-white p-8 shadow-sm">
          <div>
            <h1 className="text-2xl font-semibold text-stone-900">Create account</h1>
            <p className="mt-2 text-sm text-stone-600">
              Register a user account for your company workflow.
            </p>
          </div>

          <div className="mt-6">
            <RegisterForm />
          </div>
        </div>
      </div>
    </main>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/dashboard/page.tsx
# ============================================
"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useCompanies } from "@/features/companies/hooks/use-companies";
import { useListings } from "@/features/listings/hooks/use-listings";

export default function DashboardPage() {
  const auth = useAuthRequired();
  const listings = useListings({ page: 1, pageSize: 5 });
  const companies = useCompanies({ page: 1, pageSize: 5 });

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Dashboard"
          subtitle="Operational overview of marketplace activity and onboarding."
        />

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Authenticated user</div>
            <div className="stat-value">{auth.data?.user.email ?? "-"}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Visible listings</div>
            <div className="stat-value">{listings.data?.meta.total ?? 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Visible companies</div>
            <div className="stat-value">{companies.data?.meta.total ?? 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Company memberships</div>
            <div className="stat-value">{auth.data?.memberships.length ?? 0}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <section className="card p-6">
            <h2 className="text-lg font-semibold text-stone-900">Recent listings</h2>
            <div className="mt-4 space-y-3">
              {listings.data?.items.slice(0, 5).map((item) => (
                <div key={item.id} className="rounded-lg border border-stone-200 p-4">
                  <div className="font-medium">{item.materialCategory} / {item.materialSubtype}</div>
                  <div className="mt-1 text-sm text-stone-600">
                    {item.quantity} {item.unit} -  {item.originLocation}
                  </div>
                </div>
              ))}
              {!listings.data?.items.length ? <div className="empty-state">No listings available.</div> : null}
            </div>
          </section>

          <section className="card p-6">
            <h2 className="text-lg font-semibold text-stone-900">Recent companies</h2>
            <div className="mt-4 space-y-3">
              {companies.data?.items.slice(0, 5).map((item) => (
                <div key={item.id} className="rounded-lg border border-stone-200 p-4">
                  <div className="font-medium">{item.legalName}</div>
                  <div className="mt-1 text-sm text-stone-600">
                    {item.city}, {item.countryCode} -  {item.companyType}
                  </div>
                </div>
              ))}
              {!companies.data?.items.length ? <div className="empty-state">No companies available.</div> : null}
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/listings/page.tsx
# ============================================
"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { ListingFilters } from "@/features/listings/components/listing-filters";
import { ListingsTable } from "@/features/listings/components/listings-table";
import { useListings } from "@/features/listings/hooks/use-listings";
import type { ListingFilters as ListingFiltersType } from "@/features/listings/types";

export default function ListingsPage() {
  useAuthRequired();
  const [filters, setFilters] = useState<ListingFiltersType>({ page: 1, pageSize: 20 });
  const listings = useListings(filters);

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Listings"
          subtitle="Browse structured material listings and filter by operational criteria."
          actions={
            <Link href="/listings/new">
              <Button>Create listing</Button>
            </Link>
          }
        />

        <ListingFilters initialValue={filters} onApply={setFilters} />

        {listings.isLoading ? (
          <div className="empty-state">Loading listings...</div>
        ) : (
          <ListingsTable rows={listings.data?.items ?? []} />
        )}
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/listings/new/page.tsx
# ============================================
"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { ListingForm } from "@/features/listings/components/listing-form";

export default function NewListingPage() {
  useAuthRequired();

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Create listing"
          subtitle="Create a structured material listing aligned with the marketplace workflow."
        />
        <ListingForm mode="create" />
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/listings/[listingId]/page.tsx
# ============================================
"use client";

import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useListing } from "@/features/listings/hooks/use-listing";

type Props = {
  params: {
    listingId: string;
  };
};

export default function ListingDetailPage({ params }: Props) {
  useAuthRequired();
  const listing = useListing(params.listingId);

  if (listing.isLoading) {
    return (
      <AppShell>
        <div className="empty-state">Loading listing...</div>
      </AppShell>
    );
  }

  const item = listing.data?.data;

  if (!item) {
    return (
      <AppShell>
        <div className="empty-state">Listing not found.</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title={`${item.materialCategory} / ${item.materialSubtype}`}
          subtitle="Structured listing detail and commercial metadata."
          actions={
            <Link href={`/listings/${item.id}/edit`}>
              <Button variant="secondary">Edit listing</Button>
            </Link>
          }
        />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr_1fr]">
          <section className="card p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <div className="muted">Status</div>
                <div className="mt-1"><StatusBadge status={item.status} /></div>
              </div>
              <div>
                <div className="muted">Quantity</div>
                <div className="mt-1 font-medium">{item.quantity} {item.unit}</div>
              </div>
              <div>
                <div className="muted">Origin location</div>
                <div className="mt-1 font-medium">{item.originLocation}</div>
              </div>
              <div>
                <div className="muted">Price model</div>
                <div className="mt-1 font-medium">{item.priceModel}</div>
              </div>
              <div>
                <div className="muted">Purity indicator</div>
                <div className="mt-1 font-medium">{item.purityIndicator ?? "-"}</div>
              </div>
              <div>
                <div className="muted">Seller company ID</div>
                <div className="mt-1 break-all font-medium">{item.sellerCompanyId}</div>
              </div>
            </div>

            <div className="mt-6">
              <div className="muted">Contamination notes</div>
              <div className="mt-2 whitespace-pre-wrap rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm text-stone-800">
                {item.contaminationNotes ?? "No contamination notes provided."}
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <div className="muted">Pickup terms</div>
                <div className="mt-2 whitespace-pre-wrap rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm text-stone-800">
                  {item.pickupTerms ?? "No pickup terms."}
                </div>
              </div>
              <div>
                <div className="muted">Delivery terms</div>
                <div className="mt-2 whitespace-pre-wrap rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm text-stone-800">
                  {item.deliveryTerms ?? "No delivery terms."}
                </div>
              </div>
            </div>
          </section>

          <aside className="card p-6">
            <h2 className="text-lg font-semibold text-stone-900">Availability</h2>
            <div className="mt-4 space-y-3 text-sm">
              <div>
                <div className="muted">Start</div>
                <div className="mt-1 font-medium">{item.availabilityStart ?? "-"}</div>
              </div>
              <div>
                <div className="muted">End</div>
                <div className="mt-1 font-medium">{item.availabilityEnd ?? "-"}</div>
              </div>
              <div>
                <div className="muted">Created at</div>
                <div className="mt-1 font-medium">{item.createdAt}</div>
              </div>
              <div>
                <div className="muted">Updated at</div>
                <div className="mt-1 font-medium">{item.updatedAt}</div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/listings/[listingId]/edit/page.tsx
# ============================================
"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { ListingForm } from "@/features/listings/components/listing-form";
import { useListing } from "@/features/listings/hooks/use-listing";

type Props = {
  params: {
    listingId: string;
  };
};

export default function EditListingPage({ params }: Props) {
  useAuthRequired();
  const listing = useListing(params.listingId);

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Edit listing"
          subtitle="Update material data while preserving workflow consistency."
        />
        {listing.isLoading ? (
          <div className="empty-state">Loading listing...</div>
        ) : listing.data?.data ? (
          <ListingForm mode="edit" initialData={listing.data.data} />
        ) : (
          <div className="empty-state">Listing not found.</div>
        )}
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/companies/page.tsx
# ============================================
"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { CompaniesTable } from "@/features/companies/components/companies-table";
import { useCompanies } from "@/features/companies/hooks/use-companies";

export default function CompaniesPage() {
  useAuthRequired();
  const [q, setQ] = useState("");
  const companies = useCompanies({ page: 1, pageSize: 20, q });

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Companies"
          subtitle="Manage company records, verification states and capability profiles."
        />

        <div className="card p-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-[1fr_auto]">
            <FormField label="Search companies">
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Legal name, trading name, registration number" />
            </FormField>
            <div className="flex items-end">
              <Button type="button" variant="secondary">Search</Button>
            </div>
          </div>
        </div>

        {companies.isLoading ? (
          <div className="empty-state">Loading companies...</div>
        ) : (
          <CompaniesTable rows={companies.data?.items ?? []} />
        )}
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/companies/[companyId]/page.tsx
# ============================================
"use client";

import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { useCompany } from "@/features/companies/hooks/use-company";

type Props = {
  params: {
    companyId: string;
  };
};

export default function CompanyDetailPage({ params }: Props) {
  useAuthRequired();
  const company = useCompany(params.companyId);

  if (company.isLoading) {
    return (
      <AppShell>
        <div className="empty-state">Loading company...</div>
      </AppShell>
    );
  }

  const item = company.data?.data;

  if (!item) {
    return (
      <AppShell>
        <div className="empty-state">Company not found.</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title={item.legalName}
          subtitle="Company profile, capabilities and verification metadata."
        />

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr_1fr]">
          <section className="card p-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <div className="muted">Status</div>
                <div className="mt-1"><StatusBadge status={item.status} /></div>
              </div>
              <div>
                <div className="muted">Company type</div>
                <div className="mt-1 font-medium">{item.companyType}</div>
              </div>
              <div>
                <div className="muted">Registration number</div>
                <div className="mt-1 font-medium">{item.registrationNumber}</div>
              </div>
              <div>
                <div className="muted">Tax identifier</div>
                <div className="mt-1 font-medium">{item.taxIdentifier ?? "-"}</div>
              </div>
              <div>
                <div className="muted">Email</div>
                <div className="mt-1 font-medium">{item.email ?? "-"}</div>
              </div>
              <div>
                <div className="muted">Phone</div>
                <div className="mt-1 font-medium">{item.phone ?? "-"}</div>
              </div>
              <div>
                <div className="muted">Country</div>
                <div className="mt-1 font-medium">{item.countryCode}</div>
              </div>
              <div>
                <div className="muted">City</div>
                <div className="mt-1 font-medium">{item.city}</div>
              </div>
            </div>

            <div className="mt-6">
              <div className="muted">Address</div>
              <div className="mt-2 rounded-lg border border-stone-200 bg-stone-50 p-4 text-sm text-stone-800">
                {item.addressLine1}
                {item.addressLine2 ? <><br />{item.addressLine2}</> : null}
                <br />
                {item.postalCode} {item.city}
              </div>
            </div>
          </section>

          <aside className="card p-6">
            <h2 className="text-lg font-semibold text-stone-900">Capabilities</h2>
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span>Seller</span>
                <span className="font-medium">{item.sellerCapability ? "Yes" : "No"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Buyer</span>
                <span className="font-medium">{item.buyerCapability ? "Yes" : "No"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Logistics</span>
                <span className="font-medium">{item.logisticsCapability ? "Yes" : "No"}</span>
              </div>
              <div className="border-t border-stone-200 pt-3">
                <div className="muted">Verified at</div>
                <div className="mt-1 font-medium">{item.verifiedAt ?? "-"}</div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

# ============================================
# FILE: apps/web/src/app/(protected)/admin/users/page.tsx
# ============================================
"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { Select } from "@/components/ui/select";
import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";
import { AdminUsersTable } from "@/features/admin/components/admin-users-table";
import { useAdminUsers } from "@/features/admin/hooks/use-admin-users";

export default function AdminUsersPage() {
  useAuthRequired();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const users = useAdminUsers({ page: 1, pageSize: 20, q, status: status || undefined });

  return (
    <AppShell>
      <div className="section-stack">
        <PageHeader
          title="Admin users"
          subtitle="Operational view of platform users and account status."
        />

        <div className="card p-4">
          <div className="filters-grid">
            <FormField label="Search users">
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Email, first name, last name" />
            </FormField>
            <FormField label="Status">
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="">All</option>
                <option value="invited">invited</option>
                <option value="active">active</option>
                <option value="suspended">suspended</option>
                <option value="deactivated">deactivated</option>
              </Select>
            </FormField>
          </div>
        </div>

        {users.isLoading ? (
          <div className="empty-state">Loading users...</div>
        ) : (
          <AdminUsersTable rows={users.data?.items ?? []} />
        )}
      </div>
    </AppShell>
  );
}
