import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Optimizes for Docker
  reactStrictMode: true,
};

export default nextConfig;
