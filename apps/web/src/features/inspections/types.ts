export type InspectionState =
  | 'created'
  | 'room_created'
  | 'requested'
  | 'accepted'
  | 'live'
  | 'ended';

export interface InspectionData {
  id: string;
  listingId: string;
  roomId: string | null;
  ownerUserId: string;
  ownerCompanyId: string;
  viewerUserId: string | null;
  viewerCompanyId: string | null;
  viewerThreadId: string | null;
  state: InspectionState;
  consentToRecord: boolean;
  createdAt: string;
  updatedAt: string;
  endedAt: string | null;
}

export interface CreateInspectionResponse {
  inspection: InspectionData;
  role: 'publisher';
  publishUrl: string;
  expiresIn: number;
}

export interface JoinInspectionResponse {
  inspection: InspectionData;
  role: 'viewer';
  viewerUrl: string;
  expiresIn: number;
  roomId: string | null;
}

export interface ActiveInspectionResponse {
  inspection: InspectionData | null;
  canPublish: boolean;
  canJoin: boolean;
  isViewer: boolean;
}

export interface PublisherLinkResponse {
  role: 'publisher';
  publishUrl: string;
  expiresIn: number;
}
