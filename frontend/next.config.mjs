import path from "node:path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(process.cwd()),
  async rewrites() {
    return [
      { source: "/rag", destination: "http://127.0.0.1:8000/rag" },
      { source: "/docs", destination: "http://127.0.0.1:8000/docs" },
      { source: "/openapi.json", destination: "http://127.0.0.1:8000/openapi.json" },
    ];
  },
};

export default nextConfig;
