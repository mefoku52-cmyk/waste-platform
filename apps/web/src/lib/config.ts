export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1',
  isServer: typeof window === 'undefined',
};
