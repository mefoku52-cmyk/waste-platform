import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../api';

export const useDocuments = () =>
  useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(),
  });
