/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8083/api/:path*',
      },
      {
        source: '/agents/:path*',
        destination: 'http://localhost:8091/:path*',
      },
    ];
  },
  // Increase timeout for long-running requests (like LLM refactoring)
  serverRuntimeConfig: {
    // This doesn't directly control proxy timeout, but helps with overall server config
  },
  // Note: Next.js rewrites don't have a direct timeout config
  // The timeout is controlled by the underlying HTTP client
};

module.exports = nextConfig;
