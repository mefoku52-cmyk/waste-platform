/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const API_PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://localhost:8001';
    return [
      {
        source: '/api/v1/:path*',
        destination: `${API_PROXY_TARGET}/api/v1/:path*`,
      },
    ];
  },
  reactStrictMode: true,
};

module.exports = nextConfig;
