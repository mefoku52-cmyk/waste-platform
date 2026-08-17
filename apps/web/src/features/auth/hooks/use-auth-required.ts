import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from './use-current-user';
import { tokenStore } from '../../../lib/auth/token-store';

export const useAuthRequired = () => {
  const { data: user, isLoading, isError, isFetching } = useCurrentUser();
  const router = useRouter();
  const token = tokenStore.getToken();

  useEffect(() => {
    if (isLoading || isFetching) return;
    // žiadny token = login
    if (!token) {
      router.push('/login');
      return;
    }
    // token je, user null len po 401 (clearToken) – nie pri sieťovej chybe
    if (!user && !isError) {
      router.push('/login');
    }
  }, [user, isLoading, isFetching, isError, token, router]);

  return { user, isLoading: isLoading || isFetching };
};
