/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'github.com',
      },
      {
        protocol: 'https',
        hostname: '*.gravatar.com',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_VERSION: '1.0.0',
  },
};

module.exports = nextConfig;
