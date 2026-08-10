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
        const me: any = await authApi.getMe();
        // Backend: { user, memberships, roleCodes }
        if (me?.user) {
          return {
            ...me.user,
            email: me.user.email,
            firstName: me.user.firstName ?? me.user.first_name,
            lastName: me.user.lastName ?? me.user.last_name,
            role: me.roleCodes?.[0] || me.user.role,
            memberships: me.memberships || [],
            roleCodes: me.roleCodes || [],
          } as User;
        }
        return me as User;
      } catch (error) {
        return null;
      }
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 5,
  });
};
