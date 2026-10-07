export const config = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    '/api/v1',
  isServer: typeof window === 'undefined',

  metaPixelId: (process.env.NEXT_PUBLIC_META_PIXEL_ID || '').trim(),
};
