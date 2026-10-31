import { useQuery } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { User } from '../types';

export const useCurrentUser = () => {
  const token = tokenStore.getToken();

  return useQuery<User | null>({
    queryKey: ['auth-user', token],
    queryFn: async () => {
      try {
        if (!tokenStore.getToken()) {
          const session = await authApi.refreshBrowser();
          if (!session.accessToken) return null;
          tokenStore.setToken(session.accessToken);
        }
        const me: any = await authApi.getMe();
        if (me?.user) {
          return {
            ...me.user,
            email: me.user.email,
            firstName: me.user.firstName ?? me.user.first_name,
            lastName: me.user.lastName ?? me.user.last_name,
            role: me.roleCodes?.[0] || me.user.role,
            memberships: me.memberships || [],
            roleCodes: me.roleCodes || [],
            isPlatformAdmin: Boolean(me.isPlatformAdmin),
          } as User;
        }
        return me as User;
      } catch (error: any) {
        // Iba skutočné odhlásenie
        if (error?.status === 401) {
          tokenStore.clearToken();
          return null;
        }
        // sieť / 500 – nevyhadzuj session
        throw error;
      }
    },
    enabled: true,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
};
