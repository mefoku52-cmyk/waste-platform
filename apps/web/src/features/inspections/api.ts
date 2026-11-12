import { http } from '../../lib/api/http';
import type {
  ActiveInspectionResponse,
  CreateInspectionResponse,
  InspectionData,
  JoinInspectionResponse,
  PublisherLinkResponse,
} from './types';

export const inspectionsApi = {
  activeForListing: (listingId: string) =>
    http.get<ActiveInspectionResponse>(`/inspections?listingId=${encodeURIComponent(listingId)}`),

  create: (listingId: string) =>
    http.post<CreateInspectionResponse>('/inspections', { listingId }),

  join: (data: { listingId?: string; inspectionId?: string; threadId?: string; waitRoomSeconds?: number }) =>
    http.post<JoinInspectionResponse>('/inspections/join', data),

  get: (inspectionId: string) =>
    http.get<{ data: InspectionData }>(`/inspections/${inspectionId}`),

  publisherLink: (inspectionId: string) =>
    http.post<PublisherLinkResponse>(`/inspections/${inspectionId}/publisher-link`, {}),

  end: (inspectionId: string) =>
    http.post<{ data: InspectionData }>(`/inspections/${inspectionId}/end`, {}),

  grantRecordingConsent: (inspectionId: string) =>
    http.post<{ data: InspectionData }>(`/inspections/${inspectionId}/recording-consent`, {}),
};
