import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { LoginInput } from '../schemas';

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginInput) =>
      authApi.login({ email: data.email, password: data.password }),
    onSuccess: (response: any, variables) => {
      const remember = variables.remember !== false;
      tokenStore.setToken(response.accessToken, remember);
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });
};
