import type { NextConfig } from "next";

// The game server is an API only (SPEC §6.2). Bundles, ground truth and origins stay here
// (invariant I1); responses are built by src/lib/view.ts and checked by the leak tests.
const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "no-referrer" },
  { key: "X-Robots-Tag", value: "noindex, nofollow" },
  { key: "Cache-Control", value: "no-store" },
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // postgres is a Node-only client; keep it out of the server bundle.
  serverExternalPackages: ["postgres"],
  // The workspace packages ship TypeScript source.
  transpilePackages: ["@nidana/contracts", "@nidana/engine"],
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
