import { http } from '../../lib/api/http';
import { PaginatedResponse } from '../../lib/types/common';
import { AdminStats, UserManagement } from './types';

export const adminApi = {
  getStats: () => 
    http.get<AdminStats>('/admin/stats'),
  
  getUsers: (params?: Record<string, any>) => 
    http.get<PaginatedResponse<UserManagement>>('/admin/users', { ...params }),
  
  toggleUserStatus: (userId: string) => 
    http.post(`/admin/users/${userId}/toggle-status`, {}),
};
