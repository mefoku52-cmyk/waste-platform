import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '../api';
import { CompanyInput } from '../schemas';

export const useCreateCompany = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CompanyInput) => companiesApi.createCompany(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
};
