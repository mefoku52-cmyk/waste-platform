import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { companyPagesApi } from '../api';
import { CompanyPageUpsertInput } from '../types';

export const companyPageKeys = {
  page: (companyId: string) => ['company-page', companyId] as const,
  photos: (companyId: string) => ['company-photos', companyId] as const,
};

/** Editor dáta verejnej stránky (draft alebo published). */
export function useCompanyPage(companyId: string) {
  return useQuery({
    queryKey: companyPageKeys.page(companyId),
    queryFn: () => companyPagesApi.getPage(companyId),
    enabled: Boolean(companyId),
    retry: 1,
  });
}

/** Fotogaléria firmy. */
export function useCompanyPhotos(companyId: string) {
  return useQuery({
    queryKey: companyPageKeys.photos(companyId),
    queryFn: () => companyPagesApi.listPhotos(companyId),
    enabled: Boolean(companyId),
    retry: 1,
  });
}

export function useSaveCompanyPage(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CompanyPageUpsertInput) =>
      companyPagesApi.savePage(companyId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.page(companyId) });
    },
  });
}

export function usePublishCompanyPage(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => companyPagesApi.publish(companyId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.page(companyId) });
    },
  });
}

export function useUnpublishCompanyPage(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => companyPagesApi.unpublish(companyId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.page(companyId) });
    },
  });
}

export function useAddCompanyPhoto(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { fileUrl: string; caption?: string | null; altText?: string | null }) =>
      companyPagesApi.addPhoto(companyId, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.photos(companyId) });
    },
  });
}

export function useUpdateCompanyPhoto(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      photoId: string;
      caption?: string | null;
      altText?: string | null;
    }) =>
      companyPagesApi.updatePhoto(companyId, vars.photoId, {
        caption: vars.caption,
        altText: vars.altText,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.photos(companyId) });
    },
  });
}

export function useDeleteCompanyPhoto(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (photoId: string) => companyPagesApi.deletePhoto(companyId, photoId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.photos(companyId) });
    },
  });
}

export function useReorderCompanyPhotos(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (orderedIds: string[]) =>
      companyPagesApi.reorderPhotos(companyId, orderedIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.photos(companyId) });
    },
  });
}

export function useSetPrimaryCompanyPhoto(companyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (photoId: string) => companyPagesApi.setPrimaryPhoto(companyId, photoId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: companyPageKeys.photos(companyId) });
    },
  });
}
