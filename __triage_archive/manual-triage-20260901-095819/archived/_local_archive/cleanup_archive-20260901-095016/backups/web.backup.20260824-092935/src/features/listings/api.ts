import { http } from '../../lib/api/http';
import { PaginatedResponse } from '../../lib/types/common';
import { Listing } from './types';
import { ListingInput } from './schemas';

export const listingsApi = {
  getListings: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>('/api/v1/listings', { ...params }),

  getMarketplace: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>('/api/v1/listings/marketplace', { ...params }),

  getListing: (id: string) =>
    http.get<Listing>(`/api/v1/listings/${id}`),

  createListing: (data: ListingInput) =>
    http.post<Listing>('/api/v1/listings', data),

  updateListing: (id: string, data: Partial<ListingInput> & { status?: string }) =>
    http.put<Listing>(`/api/v1/listings/${id}`, data),

  publishListing: (id: string) =>
    http.post<{ data: any }>(`/api/v1/listings/${id}/publish`, {}),

  deleteListing: (id: string) =>
    http.delete(`/api/v1/listings/${id}`),

  getMatches: (materialType: string, params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>(`/api/v1/listings/matches?materialType=${encodeURIComponent(materialType)}`, { ...params }),
};
