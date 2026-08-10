import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      tokenStore.clearToken();
      queryClient.setQueryData(['auth-user'], null);
      queryClient.clear();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    },
  });
};
