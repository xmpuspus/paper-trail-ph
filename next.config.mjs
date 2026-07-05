/** @type {import('next').NextConfig} */
// v1 is a fully static site: all data is baked into public/data/*.json at build
// time by scripts/build_graph.py. The old FastAPI proxy is only wired when a
// BACKEND_URL is explicitly set (local development against a live backend).
const nextConfig = {
  async rewrites() {
    if (!process.env.BACKEND_URL) return [];
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
