import type { NextConfig } from "next";

// The Studio is private and read-only (SPEC §8). No image optimisation or
// remote patterns yet: figures arrive in L0.8.
const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  // postgres is a Node-only client; keep it out of the server bundle.
  serverExternalPackages: ["postgres"],
};

export default nextConfig;
