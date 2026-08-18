import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const refreshToken = tokenStore.getRefreshToken();

      if (refreshToken) {
        await authApi.logout(refreshToken);
      }

      return true;
    },
    onSettled: async () => {
      tokenStore.clearToken();
      await queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });
};
