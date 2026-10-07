import { http } from '../../lib/api/http';
import { PaginatedResponse } from '../../lib/types/common';
import { Listing } from './types';
import { ListingInput } from './schemas';

export const listingsApi = {
  getListings: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>('/listings', { ...params }),

  getMarketplace: (params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>('/listings/marketplace', { ...params }),

  getListing: (id: string) =>
    http.get<Listing>(`/listings/${id}`),

  createListing: (data: ListingInput) =>
    http.post<Listing>('/listings', data),

  // Backend vystavuje PATCH /listings/{id} (nie PUT). PUT vracalo 405.
  updateListing: (id: string, data: Partial<ListingInput> & { status?: string }) =>
    http.patch<Listing>(`/listings/${id}`, data),

  publishListing: (id: string) =>
    http.post<{ data: any }>(`/listings/${id}/publish`, {}),

  deleteListing: (id: string) =>
    http.delete(`/listings/${id}`),

  recordView: (id: string) =>
    http.post<{ ok: boolean }>(`/listings/${id}/view`, {}),

  getStats: (id: string) =>
    http.get<{ views: number; uniqueViewers: number }>(`/listings/${id}/stats`),

  getMatches: (materialType: string, params?: Record<string, any>) =>
    http.get<PaginatedResponse<Listing>>(`/listings/matches?materialType=${encodeURIComponent(materialType)}`, { ...params }),

  // AI draft — vyžaduje AI tier firmy (backend vráti 403 pre FREE/PRO)
  aiDraft: (prompt: string) =>
    http.post<{ data: AiDraftData; provider: string }>('/listings/ai-draft', { prompt }),
};

export type AiDraftData = {
  title?: string;
  description?: string;
  materialType?: string | null;
  quantity?: number | null;
  unit?: string | null;
  location?: string | null;
  condition?: string | null;
  currency?: string | null;
  price?: number | null;
};
