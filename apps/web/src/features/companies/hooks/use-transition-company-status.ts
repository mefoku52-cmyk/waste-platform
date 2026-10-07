import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '../api';

export const useTransitionCompanyStatus = (companyId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (toStatus: string) =>
      companiesApi.transitionStatus(companyId, toStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['company', companyId] });
    },
  });
};
