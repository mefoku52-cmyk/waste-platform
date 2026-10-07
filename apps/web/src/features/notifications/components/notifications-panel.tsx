'use client';

import { useNotifications } from '../hooks/use-notifications';
import { useT } from '@/lib/i18n/context';

export const NotificationsPanel = () => {
  const { t } = useT();
  const { data, isLoading, error } = useNotifications();
  const items = (data as any)?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-gray-500">{t('notifications.loading')}</div>;
  }
  if (error) {
    return (
      <div className="text-sm text-red-600">
        {t('notifications.error')}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">{t('notifications.title')}</h2>
        <span className="text-xs text-gray-500">{items.length}</span>
      </div>
      <ul className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
        {items.length === 0 ? (
          <li className="px-4 py-6 text-center text-sm text-gray-500">
            {t('notifications.empty')}
          </li>
        ) : (
          items.map((n: any) => (
            <li
              key={n.id}
              className={`px-4 py-3 text-sm ${
                n.isRead || n.is_read ? 'opacity-60' : 'bg-amber-50'
              }`}
            >
              <div className="font-medium text-gray-900">{n.title}</div>
              <div className="text-gray-600 mt-0.5">{n.message}</div>
              <div className="text-xs text-gray-400 mt-1">{n.type}</div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
};
