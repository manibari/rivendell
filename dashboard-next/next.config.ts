import type { NextConfig } from "next";

// Proxy /api/* to the FastAPI backend SERVER-SIDE, so the browser only ever talks
// to this same origin (:3000). The target is resolved on the Next server — which
// is co-located with the API on the same host (mac launchd / WSL systemd) — so
// 127.0.0.1:8000 is correct there, and the client bundle never bakes in a host.
// This is what lets the dashboard work when accessed from another machine via a
// tunnel (NEXT_PUBLIC_API_URL=localhost would have pinned the bundle to loopback).
// Override the backend location with API_PROXY_TARGET if it isn't local.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Alternate build output dir, used by bin/sk-tester-cron so its nightly
  // build-check NEVER replaces the live .next under the running prod server
  // (doing so 500s every static asset — broke the dashboard 2026-07-05 and
  // 2026-07-13). Unset = normal ".next".
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_PROXY_TARGET}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
