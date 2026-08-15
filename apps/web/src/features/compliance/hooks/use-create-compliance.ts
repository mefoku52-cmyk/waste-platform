import { useMutation, useQueryClient } from '@tanstack/react-query';
import { complianceApi } from '../api';

export const useCreateCompliance = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: complianceApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['compliance'] }),
  });
};
