import { useQuery } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { User } from '../types';

export const useCurrentUser = () => {
  const token = tokenStore.getToken();

  return useQuery<User | null>({
    queryKey: ['auth-user'],
    queryFn: async () => {
      if (!token) return null;
      try {
        return await authApi.getMe();
      } catch (error) {
        return null;
      }
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 5, // 5 minút
  });
};
