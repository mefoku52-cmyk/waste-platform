/** @type {
  allowedDevOrigins: ['127.0.0.1', 'localhost'],
import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://cmep-api:8000/api/v1/:path*',
      },
    ];
  },
  reactStrictMode: true,
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname)
};

module.exports = nextConfig;
