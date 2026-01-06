import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Optimizes for Docker
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true, // Railway builds can be strict
  },
  typescript: {
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
