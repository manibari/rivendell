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
