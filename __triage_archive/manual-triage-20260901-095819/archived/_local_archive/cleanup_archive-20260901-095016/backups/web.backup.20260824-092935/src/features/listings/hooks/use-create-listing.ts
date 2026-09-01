import { useMutation, useQueryClient } from '@tanstack/react-query';
import { listingsApi } from '../api';
import { ListingInput } from '../schemas';

export const useCreateListing = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ListingInput) => listingsApi.createListing(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] });
    },
  });
};
