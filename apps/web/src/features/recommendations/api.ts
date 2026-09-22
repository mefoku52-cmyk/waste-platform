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

function errorDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0] && typeof detail[0] === 'object') {
    const first = detail[0] as { msg?: string };
    return first.msg || fallback;
  }
  return fallback;
}

export async function getListingRecommendations(listingId: string): Promise<RecommendationsResponse> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(config.apiBaseUrl + '/recommendations/listings/' + listingId, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(errorDetail(body, 'HTTP ' + res.status + ' Recommendations request failed'));
  }
  return body as RecommendationsResponse;
}

export async function postListingViewed(listingId: string): Promise<void> {
  const token = localStorage.getItem('accessToken');
  const res = await fetch(config.apiBaseUrl + '/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
    body: JSON.stringify({ eventType: 'listing_viewed', listingId }),
  });
  if (!res.ok) return;
}
