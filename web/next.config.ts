import type { NextConfig } from "next";
const apiOrigin=process.env.FNS_API_ORIGIN || "http://127.0.0.1:8000";
if(!["http://127.0.0.1:8000","http://api:8000"].includes(apiOrigin)) throw new Error("Only the independent local API is allowed");
const config: NextConfig = {
  experimental: { proxyClientMaxBodySize: "50mb" },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiOrigin}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};
export default config;
