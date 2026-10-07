import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '../api';
import { CompanyInput } from '../schemas';

export const useUpdateCompany = (companyId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CompanyInput>) =>
      companiesApi.updateCompany(companyId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['company', companyId] });
    },
  });
};
