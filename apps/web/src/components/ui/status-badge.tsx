import * as React from 'react';
import { cn } from '../../lib/utils/cn';

type StatusType = 'active' | 'completed' | 'cancelled' | 'pending' | 'verified' | 'unverified';

interface StatusBadgeProps {
  status: StatusType | string;
  className?: string;
}

const statusStyles: Record<string, string> = {
  active: 'bg-green-100 text-green-800 border-green-200',
  verified: 'bg-blue-100 text-blue-800 border-blue-200',
  completed: 'bg-gray-100 text-gray-800 border-gray-200',
  pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  cancelled: 'bg-red-100 text-red-800 border-red-200',
  unverified: 'bg-gray-100 text-gray-600 border-gray-200',
};

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  const style = statusStyles[status.toLowerCase()] || 'bg-gray-100 text-gray-600 border-gray-200';
  
  return (
    <span className={cn(
      "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
      style,
      className
    )}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};
