'use client';

import { useAdminUsers } from '../hooks/use-admin-users';
import { cn } from '../../../lib/utils/cn';

export const AdminUsersTable = () => {
  const { data, isLoading, error } = useAdminUsers();

  if (isLoading) return <div className="p-4 text-center text-gray-600">Načítavam používateľov...</div>;
  if (error) return <div className="p-4 text-red-500 text-center font-medium">Chyba pri načítaní používateľov.</div>;

  const users = data?.data || [];

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm bg-white">
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
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500 italic">
                Žiadni používatelia neboli nájdení.
              </td>
            </tr>
          ) : (
            users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900">{user.first_name} {user.last_name}</td>
                <td className="px-4 py-3 text-gray-600">{user.email}</td>
                <td className="px-4 py-3">
                  <span className="capitalize px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs">
                    {user.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={cn(
                    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                    user.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  )}>
                    {user.is_active ? 'Aktívny' : 'Deaktivovaný'}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
