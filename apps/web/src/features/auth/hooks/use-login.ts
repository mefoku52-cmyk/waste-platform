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
    onSuccess: (response: LoginResponse, variables) => {
      // Ak je aktivna 2FA, NEUKLADAME tokeny (ziadne este neprisli).
      // Caller (login-form) musi spravit druhy krok.
      if (response.requires2fa) {
        return;
      }
      if (!response.accessToken || !response.refreshToken) {
        return;
      }
      const remember = variables.remember !== false;
      tokenStore.setTokens(
        response.accessToken,
        response.refreshToken,
        remember,
      );
      queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });
};
