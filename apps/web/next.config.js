/** @type {import('next').NextConfig} */
const path = require('path');

// Ciel server-side API proxy (build-time hodnota).
// - docker-compose: predvolena hodnota `http://cmep-api:8000` (service name).
// - Render / ine prostredie: nastav `API_PROXY_TARGET` na realnu URL API sluzby
//   PRED buildom web image. Hostname z docker-compose sa v cloude nerozlisuje.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://cmep-api:8000';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${API_PROXY_TARGET}/api/v1/:path*`,
      },
    ];
  },
  reactStrictMode: true,
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname),
};

module.exports = nextConfig;