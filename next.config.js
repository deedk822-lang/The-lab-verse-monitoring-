/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Don't fail the build on ESLint errors during development
    // but still run linting
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Don't fail the build on TypeScript errors during development
    ignoreBuildErrors: false,
  },
  // Optimize for Vercel deployment
  swcMinify: true,
  // Configure experimental features if needed
  experimental: {
    // Add any experimental features here
  },
  // Configure webpack if needed
  webpack: (config, { isServer }) => {
    // Add any custom webpack configuration here
    return config;
  },
};

module.exports = nextConfig;
