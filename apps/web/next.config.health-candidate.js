/** @type {import('next').NextConfig} */

const SECURITY_HEADERS = [
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=(), payment=()' },
  { key: 'X-Permitted-Cross-Domain-Policies', value: 'none' },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  async headers() {
    return [{ source: '/:path*', headers: SECURITY_HEADERS }];
  },
  async rewrites() {
    const API_PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://localhost:8001';
    return [
      {
        source: '/api/v1/health',
        destination: `${API_PROXY_TARGET}/health`,
      },
      {
        source: '/api/v1/ready',
        destination: `${API_PROXY_TARGET}/ready`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${API_PROXY_TARGET}/api/v1/:path*`,
      },
    ];
  },
  reactStrictMode: true,
};

module.exports = nextConfig;
