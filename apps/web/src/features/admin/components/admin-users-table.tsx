'use client';

import { useAdminUsers } from '../hooks/use-admin-users';
import type { UserManagement } from '../types';
import { cn } from '../../../lib/utils/cn';
import { useT } from '@/lib/i18n/context';

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
            <th className="px-4 py-3 text-left font-semibold text-gray-900">{t('tables.name')}</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">E-mail</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">{t('tables.role')}</th>
            <th className="px-4 py-3 text-left font-semibold text-gray-900">{t('tables.status')}</th>
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
