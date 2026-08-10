import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from './use-current-user';
import { tokenStore } from '../../../lib/auth/token-store';

export const useAuthRequired = () => {
  const { data: user, isLoading } = useCurrentUser();
  const router = useRouter();
  const token = tokenStore.getToken();

  useEffect(() => {
    if (!isLoading && (!user || !token)) {
      router.push('/login');
    }
  }, [user, isLoading, token, router]);

  return { user, isLoading };
};
