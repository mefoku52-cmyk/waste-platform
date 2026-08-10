import { http } from '../../lib/api/http';
import { PaginatedResponse, ApiResponse } from '../../lib/types/common';
import { Listing } from './types';
import { ListingInput } from './schemas';

export const listingsApi = {
  getListings: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>('/api/v1/listings', { ...params }),

  getListing: (id: string) =>
    http.get<Listing>(`/api/v1/listings/${id}`),

  createListing: (data: ListingInput) =>
    http.post<Listing>('/api/v1/listings', data),

  updateListing: (id: string, data: Partial<ListingInput>) =>
    http.patch<Listing>(`/api/v1/listings/${id}`, data),

  deleteListing: (id: string) =>
    http.delete(`/api/v1/listings/${id}`),
};
