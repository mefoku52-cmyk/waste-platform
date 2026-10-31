import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';
import { LoginInput } from '../schemas';
import type { LoginResponse } from '../types';

export const useLogin = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LoginInput): Promise<LoginResponse> =>
      authApi.login({ email: data.email, password: data.password }),
    onSuccess: (response: LoginResponse) => {
      // Ak je aktivna 2FA, NEUKLADAME tokeny (ziadne este neprisli).
      // Caller (login-form) musi spravit druhy krok.
      if (response.requires2fa) {
        return;
      }
      if (!response.accessToken) {
        return;
      }
      tokenStore.setToken(response.accessToken);
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });
};
