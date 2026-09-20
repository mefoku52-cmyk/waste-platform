import { config } from '../../lib/config';

export type RecommendationCandidate = {
  companyId: string;
  legalName: string;
  city: string;
  countryCode: string;
  buyerCapability: boolean;
  logisticsCapability: boolean;
  score: number;
  reasons: string[];
};

export type RecommendationsResponse = {
  listingId: string;
  materialType: string;
  location: string;
  items: RecommendationCandidate[];
};

export async function getListingRecommendations(listingId: string): Promise<RecommendationsResponse> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(`\( {config.apiBaseUrl}/recommendations/listings/ \){listingId}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : 'Recommendations request failed';
    throw new Error(detail);
  }
  return body as RecommendationsResponse;
}
