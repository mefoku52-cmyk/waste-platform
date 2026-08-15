import { useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../api';

export const useCreateDocument = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      title: string;
      documentType: string;
      fileUrl: string;
      companyId: string;
      listingId?: string | null;
    }) => documentsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};
