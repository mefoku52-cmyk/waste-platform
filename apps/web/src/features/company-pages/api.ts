import { http } from '../../lib/api/http';
import {
  CompanyPageData,
  CompanyPageUpsertInput,
  CompanyPhotoData,
  PageResponse,
  PhotosResponse,
  ReviewData,
  ReviewsResponse,
  ReviewStatus,
  SlugAvailability,
} from './types';

export const companyPagesApi = {
  getPage: async (companyId: string): Promise<CompanyPageData> => {
    const res = await http.get<PageResponse>(`/companies/${companyId}/page`);
    return res.data;
  },

  savePage: async (
    companyId: string,
    input: CompanyPageUpsertInput,
  ): Promise<CompanyPageData> => {
    const res = await http.put<PageResponse>(`/companies/${companyId}/page`, input);
    return res.data;
  },

  publish: async (companyId: string): Promise<CompanyPageData> => {
    const res = await http.post<PageResponse>(`/companies/${companyId}/page/publish`);
    return res.data;
  },

  unpublish: async (companyId: string): Promise<CompanyPageData> => {
    const res = await http.post<PageResponse>(`/companies/${companyId}/page/unpublish`);
    return res.data;
  },

  checkSlug: (companyId: string, slug: string) =>
    http.get<SlugAvailability>(
      `/companies/${companyId}/page/slug-available?slug=${encodeURIComponent(slug)}`,
    ),

  // ── Fotogaléria ──
  listPhotos: async (companyId: string): Promise<CompanyPhotoData[]> => {
    const res = await http.get<PhotosResponse>(`/companies/${companyId}/photos`);
    return res.items;
  },

  addPhoto: async (
    companyId: string,
    input: { fileUrl: string; caption?: string | null; altText?: string | null },
  ): Promise<CompanyPhotoData[]> => {
    const res = await http.post<PhotosResponse>(`/companies/${companyId}/photos`, input);
    return res.items;
  },

  updatePhoto: async (
    companyId: string,
    photoId: string,
    input: { caption?: string | null; altText?: string | null },
  ): Promise<CompanyPhotoData[]> => {
    const res = await http.patch<PhotosResponse>(
      `/companies/${companyId}/photos/${photoId}`,
      input,
    );
    return res.items;
  },

  deletePhoto: async (companyId: string, photoId: string): Promise<CompanyPhotoData[]> => {
    const res = await http.delete<PhotosResponse>(`/companies/${companyId}/photos/${photoId}`);
    return res.items;
  },

  reorderPhotos: async (companyId: string, orderedIds: string[]): Promise<CompanyPhotoData[]> => {
    const res = await http.put<PhotosResponse>(`/companies/${companyId}/photos/order`, {
      orderedIds,
    });
    return res.items;
  },

  setPrimaryPhoto: async (companyId: string, photoId: string): Promise<CompanyPhotoData[]> => {
    const res = await http.post<PhotosResponse>(
      `/companies/${companyId}/photos/${photoId}/primary`,
    );
    return res.items;
  },

  // ── Recenzie (editor / moderácia) ──
  listReviews: (
    companyId: string,
    params?: { status?: ReviewStatus; page?: number; pageSize?: number },
  ) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.page) qs.set('page', String(params.page));
    if (params?.pageSize) qs.set('pageSize', String(params.pageSize));
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return http.get<ReviewsResponse>(`/companies/${companyId}/reviews${suffix}`);
  },

  moderateReview: async (
    companyId: string,
    reviewId: string,
    status: 'approved' | 'rejected',
  ): Promise<ReviewData> => {
    const res = await http.patch<{ data: ReviewData }>(
      `/companies/${companyId}/reviews/${reviewId}/moderate`,
      { status },
    );
    return res.data;
  },
};
