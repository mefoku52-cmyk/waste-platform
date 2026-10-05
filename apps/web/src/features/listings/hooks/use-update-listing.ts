import { useMutation, useQueryClient } from '@tanstack/react-query';
import { listingsApi } from '../api';
import { ListingInput } from '../schemas';

export const useUpdateListing = (id: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<ListingInput> & { status?: string }) =>
      listingsApi.updateListing(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
      queryClient.invalidateQueries({ queryKey: ['listing', id] });
      queryClient.invalidateQueries({ queryKey: ['marketplace'] });
    },
  });
};
