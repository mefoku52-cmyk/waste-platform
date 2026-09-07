#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT="$HOME/waste-platform"
OUTDIR="$PROJECT/scripts/grok-audit"
REPORT="$OUTDIR/apply_admin_frontend_patch_report.txt"

mkdir -p "$OUTDIR"
exec > >(tee "$REPORT") 2>&1

echo "=== APPLY ADMIN FRONTEND PATCH ==="
echo "CAS: $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "PROJEKT: $PROJECT"
echo

backup_file() {
  local f="$1"
  if [ -f "$f" ]; then
    cp "$f" "$f.bak-$(date +%Y%m%d-%H%M%S)"
    echo "[BACKUP] $f"
  else
    echo "[INFO] No existing file to back up: $f"
  fi
}

ADMIN_TYPES="$PROJECT/apps/web/src/features/admin/types.ts"
ADMIN_API="$PROJECT/apps/web/src/features/admin/api.ts"
ADMIN_HOOK="$PROJECT/apps/web/src/features/admin/hooks/use-admin-users.ts"
ADMIN_TABLE="$PROJECT/apps/web/src/features/admin/components/admin-users-table.tsx"

backup_file "$ADMIN_TYPES"
backup_file "$ADMIN_API"
backup_file "$ADMIN_HOOK"
backup_file "$ADMIN_TABLE"

cat > "$ADMIN_TYPES" <<'EOT'
import { User } from '../auth/types';

export interface AdminStats {
  total_users: number;
  total_listings: number;
  total_companies: number;
  pending_verifications: number;
}

export interface UserManagement extends User {
  is_active?: boolean;
  isActive?: boolean;
  last_login?: string;
  lastLogin?: string;
  role_codes?: string[];
  roleCodes?: string[];
}

export interface AdminUsersResponse {
  data?: UserManagement[];
  items?: UserManagement[];
  users?: UserManagement[];
  meta?: Record<string, unknown>;
}
EOT

cat > "$ADMIN_API" <<'EOT'
import { http } from '../../lib/api/http';
import type { AdminStats, AdminUsersResponse } from './types';

export const adminApi = {
  getStats: async () => http.get<AdminStats>('/admin/stats'),

  getUsers: async (_params?: Record<string, unknown>) =>
    http.get<AdminUsersResponse>('/admin/users'),

  listAudit: (params?: Record<string, unknown>) =>
    http.get<{ items: unknown[]; meta: Record<string, unknown> }>('/admin', { ...params }),
};
EOT

cat > "$ADMIN_HOOK" <<'EOT'
import { useQuery } from '@tanstack/react-query';
import { adminApi } from '../api';
import type { AdminUsersResponse } from '../types';

export const useAdminUsers = (params?: Record<string, unknown>) => {
  return useQuery<AdminUsersResponse>({
    queryKey: ['admin-users', params],
    queryFn: () => adminApi.getUsers(params),
  });
};
EOT

cat > "$ADMIN_TABLE" <<'EOT'
'use client';

import { useAdminUsers } from '../hooks/use-admin-users';
import type { UserManagement } from '../types';
import { cn } from '../../../lib/utils/cn';

function getUserList(payload: unknown): UserManagement[] {
  if (!payload || typeof payload !== 'object') return [];

  const source = payload as {
    data?: UserManagement[];
    items?: UserManagement[];
    users?: UserManagement[];
  };

  if (Array.isArray(source.data)) return source.data;
  if (Array.isArray(source.items)) return source.items;
  if (Array.isArray(source.users)) return source.users;
  return [];
}

function getUserDisplayName(user: UserManagement): string {
  const firstName = user.firstName ?? user.first_name ?? '';
  const lastName = user.lastName ?? user.last_name ?? '';
  const fullName = `${firstName} ${lastName}`.trim();

  if (fullName) return fullName;
  if (user.email) return user.email;
  return 'Neznámy používateľ';
}

function getUserRole(user: UserManagement): string {
  const role =
    user.roleCodes?.[0] ??
    user.role_codes?.[0] ??
    user.role ??
    'user';

  return String(role);
}

function getUserIsActive(user: UserManagement): boolean {
  if (typeof user.isActive === 'boolean') return user.isActive;
  if (typeof user.is_active === 'boolean') return user.is_active;

  if (typeof user.status === 'string') {
    const normalizedStatus = user.status.toLowerCase();
    if (['active', 'aktivny', 'aktívny', 'enabled'].includes(normalizedStatus)) return true;
    if (['inactive', 'disabled', 'deactivated', 'deaktivovany', 'deaktivovaný'].includes(normalizedStatus)) return false;
  }

  return false;
}

export const AdminUsersTable = () => {
  const { data, isLoading, error } = useAdminUsers();

  if (isLoading) {
    return <div className="p-4 text-center text-gray-600">Načítavam používateľov...</div>;
  }

  if (error) {
    return <div className="p-4 text-center font-medium text-red-500">Chyba pri načítaní používateľov.</div>;
  }

  const users = getUserList(data);

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">Meno</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">E-mail</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">Rola</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">Stav</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {users.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center italic text-gray-500">
                Žiadni používatelia neboli nájdení.
              </td>
            </tr>
          ) : (
            users.map((user, index) => {
              const active = getUserIsActive(user);
              const rowKey = user.id ?? user.email ?? `user-row-${index}`;

              return (
                <tr key={rowKey} className="transition-colors hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {getUserDisplayName(user)}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{user.email ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700 capitalize">
                      {getUserRole(user)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      )}
                    >
                      {active ? 'Aktívny' : 'Deaktivovaný'}
                    </span>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};
EOT

echo
echo "=== PATCHED FILES ==="
for f in "$ADMIN_TYPES" "$ADMIN_API" "$ADMIN_HOOK" "$ADMIN_TABLE"; do
  echo "--- $f"
  nl -ba "$f" | sed -n '1,260p'
  echo
done

echo "REPORT: $REPORT"
echo "=== KONIEC APPLY ADMIN FRONTEND PATCH ==="
