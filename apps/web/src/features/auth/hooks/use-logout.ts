import { useMutation, useQueryClient } from '@tanstack/react-query';

import { authApi } from '../api';
import { tokenStore } from '../../../lib/auth/token-store';

const AI_SESSION_KEY = 'cmep_ai_session_id';
const CHAT_HISTORY_KEY = 'cmep_chat_history';

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
      if (typeof window !== 'undefined') {
        localStorage.removeItem(AI_SESSION_KEY);
        localStorage.removeItem(CHAT_HISTORY_KEY);
      }
      await queryClient.invalidateQueries({ queryKey: ['auth-user'] });
    },
  });
};
