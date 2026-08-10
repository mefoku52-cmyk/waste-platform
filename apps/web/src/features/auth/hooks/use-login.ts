import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { LoginInput } from '../schemas';

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginInput) => authApi.login(data),
    onSuccess: (response) => {
      // Backend vracia accessToken, nie token
      tokenStore.setToken(response.accessToken);
      // User sa načíta samostatne cez /auth/me
    },
  });
};
